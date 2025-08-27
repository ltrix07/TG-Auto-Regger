import time
from datetime import datetime as dt
from datetime import timedelta, timezone
from market_handler.market import market, get_my_accounts
from utils import read_json, write_json


def _ceil_to_hour(t: dt) -> dt:
    """Округление вверх до начала следующего часа (или сохранение, если уже ровно час)."""
    if t.minute == 0 and t.second == 0 and t.microsecond == 0:
        return t.replace(microsecond=0)
    return (t.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))


def _ensure_datetime(x):
    if x is None:
        return None
    if isinstance(x, dt):
        return x
    if isinstance(x, str):
        # ожидаемый формат: "dd.mm.YYYY HH:MM"
        try:
            return dt.strptime(x, "%d.%m.%Y %H:%M")
        except Exception:
            # попробуем ISO-подход
            return dt.fromisoformat(x)
    raise ValueError("Unsupported time format: %r" % (x,))


def plan_boosts(now=None, last_group_start=None):
    today_date = dt.now().strftime("%Y-%m-%d")
    data_file_name = f"{today_date}_sales_report.json"

    try:
        data = read_json(data_file_name)
        top_hours_data = data[:5]
        write_json(top_hours_data, 'actual_info.json')
    except FileNotFoundError:
        top_hours_data = read_json('actual_info.json')

    if now is None:
        now = dt.now()

    planned = []
    boosts_available = 5
    six_hours = timedelta(hours=6)

    # минимальное время для нового старта = now или last_group_start + 6ч
    if last_group_start:
        next_available = max(now, last_group_start + six_hours)
    else:
        next_available = now

    # FIX: NA округляем ВВЕРХ до часа
    na_hourly = _ceil_to_hour(next_available)  # <-- ключевая правка

    today = now.date()
    candidate_hours = []
    for entry in top_hours_data:
        h = entry["hour"]
        candidate_time = dt.combine(today, dt.min.time()) + timedelta(hours=h)
        if candidate_time < now:
            candidate_time += timedelta(days=1)
        candidate_hours.append((candidate_time, entry))

    # Добавляем "искусственный" слот NA
    candidate_hours.append(
        (na_hourly, {"hour": na_hourly.hour, "sales_count": -1})
    )
    candidate_hours.sort(key=lambda x: x[0])

    # Подготовим только реальные слоты (без NA) и найдём среди них валидные (feasible)
    real_hours = [(t, e) for (t, e) in candidate_hours if e["sales_count"] != -1]
    real_hours.sort(key=lambda x: x[0])

    feasible_real = []
    for cand_time, entry in real_hours:
        if cand_time < na_hourly:
            continue
        skip = False
        cand_window_end = cand_time + six_hours
        for high_time, high_entry in real_hours:
            if high_entry["sales_count"] > entry["sales_count"]:
                if cand_time < high_time < cand_window_end:
                    skip = True
                    break
        if not skip:
            feasible_real.append((cand_time, entry))

    # шаг 1: ищем лучший слот
    best_choice = None
    for cand_time, entry in candidate_hours:
        # нельзя раньше доступного времени (учитываем округлённый NA)
        if cand_time < na_hourly:
            continue

        if entry["sales_count"] == -1:
            # FIX: NA-слот берём ТОЛЬКО если в его окне НЕТ валидных реальных слотов
            na_window_end = cand_time + six_hours
            has_feasible_in_window = any(cand_time <= t < na_window_end for (t, _) in feasible_real)
            if has_feasible_in_window:
                continue  # пропускаем NA, чтобы не блокировать более приоритетный валидный слот
            best_choice = (cand_time, entry)
            break
        else:
            # Реальный слот: стандартная проверка на перекрытие более приоритетных реальных слотов
            skip = False
            cand_window_end = cand_time + six_hours
            for high_time, high_entry in real_hours:
                if high_entry["sales_count"] > entry["sales_count"]:
                    if cand_time < high_time < cand_window_end:
                        skip = True
                        break
            if not skip:
                best_choice = (cand_time, entry)
                break

    if not best_choice:
        return []

    chosen_time, chosen_entry = best_choice

    # шаг 2: проверка дробления (оставляем как было; с NA diff всегда > 20%, поэтому дробление не сработает)
    distribution = [(chosen_time, boosts_available)]
    for cand_time, entry in candidate_hours:
        if cand_time == chosen_time:
            continue
        # оба слота >= na_hourly
        if cand_time >= na_hourly:
            # разница <6ч и приоритетность <20%
            if abs((cand_time - chosen_time).total_seconds()) < 6 * 3600:
                diff = abs(chosen_entry["sales_count"] - entry["sales_count"]) / max(chosen_entry["sales_count"], entry["sales_count"])
                if diff <= 0.2:
                    distribution = [
                        (chosen_time, 3),
                        (cand_time, 2)
                    ]
                    break

    # шаг 3: расписание по минутам
    for time_slot, count in distribution:
        interval = 60 // count
        base = time_slot.replace(minute=0, second=0, microsecond=0)
        for i in range(count):
            planned.append(base + timedelta(minutes=i * interval))

    return planned


def bump_old_item():
    my_items = get_my_accounts(
        category_id=24,
        show='active',
        origin=['autoreg'],
        spam='no',
        country_code=['US'],
        order_by='pdate_to_up'
    )

    for item in my_items:
        if item['is_sticky'] == 1:
            print(f"Товар {item['item_id']} откреплён")
            market.managing.unstick(item['item_id'])
            break

    target_item = None
    for item in my_items:
        if item['is_sticky'] == 0:
            target_item = item
            break

    response = market.managing.bump(target_item['item_id']).json()
    if 'errors' in response.json():
        print(f"Item {target_item['item_id']} can't be bump with error: {response['errors']}")
    else:
        print(f"Item {target_item['item_id']} bumped")

        status = market.managing.stick(target_item['item_id']).json()
        if 'errors' in status:
            print(f"Item {target_item['item_id']} is not sticky with error: {status['errors']}")
        if status['status'] == 'ok':
            print(f"Item {target_item['item_id']} is sticky")


def bump_old_item_loop(time_out, times):
    count = 0
    while count < times:
        my_items = get_my_accounts(
            category_id=24,
            show='active',
            origin=['autoreg'],
            spam='no',
            country_code=['US'],
            order_by='pdate_to_up'
        )
        for item in my_items:
            if item['is_sticky'] == 1:
                print(f"Item {item['item_id']} unstick")
                market.managing.unstick(item['item_id'])
                break

        target_item = my_items[0]
        response = market.managing.bump(target_item['item_id'])
        print(response.json())
        if 'errors' in response.json():
            print(f"Item {target_item['item_id']} can't be bump with: {response['error']}")
        print(f"Item {target_item['item_id']} bumped")

        market.managing.stick(target_item['item_id'])
        print(f"Item {target_item['item_id']} is sticky")
        count += 1
        time.sleep(time_out)


def auto_bump_items(poll_interval: int = 20):
    last_group_start = None
    schedule = []
    idx = 0

    while True:
        now = dt.now()

        if idx >= len(schedule):
            schedule = plan_boosts(now=now, last_group_start=last_group_start) or []
            print(schedule)
            # приводим к datetime и сортируем
            schedule = [_ensure_datetime(t) for t in schedule]
            schedule = [t for t in schedule if t is not None]
            schedule.sort()
            idx = 0

            if not schedule:
                time.sleep(poll_interval)
                continue

        next_time = schedule[idx]

        if now >= next_time:
            try:
                print(f"[{now.strftime('%d.%m.%Y %H:%M:%S')}] Bump item by slot {next_time.strftime('%d.%m.%Y %H:%M')}")
                bump_old_item()
            except Exception as exc:
                print(f"Error with bump in {next_time}: {exc}")

            # если это первый слот в группе — фиксируем начало группы
            if idx == 0:
                last_group_start = next_time

            # помечаем как обработанный, переходим к следующему
            idx += 1

            # не спим, сразу проверяем следующий слот (на случай, если он уже прошёл)
            continue

        else:
            # ждём до ближайшего слота, но не дольше poll_interval
            seconds_to_next = (next_time - now).total_seconds()
            wait = seconds_to_next if seconds_to_next <= poll_interval else poll_interval
            # добавим небольшой запас, чтобы не промазать
            if wait > 0:
                time.sleep(wait + 0.5)
            else:
                time.sleep(1)
            continue


if __name__ == '__main__':
    auto_bump_items()