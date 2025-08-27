import time
import argparse
import datetime
from market_handler.market import (market, collect_login_pass,
                                    delete_item, upload_items,
                                    DESCRIPTION)
from collections import deque


def autopost_top(args):
    # Время
    today = datetime.date.today()
    start_dt = datetime.datetime.combine(today, datetime.time.fromisoformat(args.start_time))
    end_dt = datetime.datetime.combine(today, datetime.time.fromisoformat(args.end_time)) if args.end_time else None
    delay_sec = args.base_delay * 60

    origin = 'autoreg'
    filter_country = ["US"]
    spam_filter = "no"
    extra = {"checkChannels": True, "checkSpam": True}
    debug = False

    # Сбор аккаунтов
    accounts_data = collect_login_pass(
        category_id=args.category_id,
        show='active',
        country_code=filter_country,
        spam=spam_filter,
        origin=[origin],
        write_to_file=args.write_to_file
    )
    if not accounts_data:
        print("Нет подходящих аккаунтов")
        return

    queue = deque(accounts_data.items())
    sticky_deque = deque(maxlen=3)

    now = datetime.datetime.now()
    if now < start_dt:
        wait_sec = (start_dt - now).total_seconds()
        print(f"Ожидание {wait_sec / 60:.1f} минут…")
        time.sleep(wait_sec)

    print("Начинаем ротацию аккаунтов...")

    while (args.infinite_loop or (end_dt and datetime.datetime.now() < end_dt)) and queue:
        old_item_id, acc_info = queue.popleft()

        del_resp = delete_item(old_item_id)
        if 'error' in del_resp:
            print(f"Аккаунт {old_item_id} уже недоступен (продан?), пропуск.")
            continue

        new_item_id = upload_items(
            category_id=args.category_id,
            origin=origin,
            single_acc_info=acc_info,
            description=DESCRIPTION,
            extra=extra,
            debug=debug
        )

        if new_item_id:
            queue.append((new_item_id, acc_info))
            try:
                if len(sticky_deque) >= 3:
                    old_sticky = sticky_deque[0]
                    market.managing.unstick(old_sticky)

                market.managing.stick(new_item_id)
                sticky_deque.append(new_item_id)
            except Exception as e:
                print(f"Ошибка sticky для {new_item_id}: {e}")

        time.sleep(delay_sec)

    print("Ротация завершена.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Автоматическая ротация аккаунтов")
    parser.add_argument('--start-time', required=True, help="Время старта (HH:MM)")
    parser.add_argument('--base-delay', type=int, required=True, help="Базовая задержка (в минутах)")
    parser.add_argument('--infinite-loop', action='store_true', help="Бесконечный цикл")
    parser.add_argument('--end-time', help="Время окончания (HH:MM), если не бесконечный цикл")
    parser.add_argument('--category-id', type=int, required=True, help="ID категории на маркете")
    parser.add_argument('--write-to-file', action='store_true', help="Записывать аккаунты в файл")

    args = parser.parse_args()
    autopost_top(args)
