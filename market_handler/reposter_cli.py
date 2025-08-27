from LOLZTEAM.Client import Market
from utils import write_json, read_json
import time
import argparse
import datetime
from typing import Literal
from collections import deque
import os
import signal
import sys

DESCRIPTION = """Бонус за отзыв:
Оставьте отзыв о покупке и получите скидку 10% на следующую покупку! 1 отзыв = 1 скидка. Для оптовых заказов пишите в ЛС — обсудим индивидуальные условия!
 Гарантия:
• 3 дня гарантии при условии, что аккаунт не используется для спама или действий, нарушающих правила Telegram.
• В случае проблем — оперативная поддержка.
 Важно:
В первую неделю использования обязательно подключайтесь через прокси страны регистрации аккаунта для стабильной работы.
Пишите в ЛС для заказа, уточнения деталей или оптовых предложений!
Надежность, качество, поддержка — ваш успех с нашими аккаунтами!"""

ACCOUNT_DATA_FOR_COUNTRY = {
    "US": {"title": "+1 - США | НОВЫЙ АККАУНТ | ВХОД С ЛЮБОГО УСТРОЙСТВА",
           "title_en": "+1 - USA | New account | Entrance from any device", "price": 0.93},
    "CY": {"title": "+357 КИПР | НОВЫЙ АККАУНТ | ВХОД С ЛЮБОГО УСТРОЙСТВА",
           "title_en": "+357 Cyprus | New account | Entrance from any device", "price": 4},
    "TR": {"title": "+90 ТУРЦИЯ | НОВЫЙ АККАУНТ | ВХОД С ЛЮБОГО УСТРОЙСТВА",
           "title_en": "+90 Türkiye | New account | Entrance from any device", "price": 3.5},
    "PL": {"title": "+48 ПОЛЬША | НОВЫЙ АККАУНТ | ВХОД С ЛЮБОГО УСТРОЙСТВА",
           "title_en": "+48 Poland | New account | Entrance from any device", "price": 2.4}
}

DELETED_ITEMS_PATH = 'deleted_items.json'
TOKEN_PATH = 'lzt_token.txt'
with open(TOKEN_PATH, 'rb') as file:
    TOKEN = bytes.decode(file.read())
market = Market(TOKEN)


# Обработчик SIGTERM
def signal_handler(sig, frame):
    print("Получен SIGTERM, завершаем работу...")
    sys.exit(0)  # Вызывает SystemExit, что приводит к finally

signal.signal(signal.SIGTERM, signal_handler)


def delete_item(item_id, reason='test'):
    response = market.managing.delete(item_id, reason)
    if response.status_code == 200:
        delete_from_trash = market.managing.delete(item_id, reason)
        return delete_from_trash.json()
    return response.json()


def get_my_accounts(category_id: int, show: str, origin: list, spam: str, country_code: list, order_by):
    page = 1
    items = []
    while True:
        response = market.list.owned(
            category_id=category_id,
            show=show,
            origin=origin,
            page=page,
            spam=spam,
            country=country_code,
            order_by=order_by
        )
        if response.status_code != 200:
            print("Превышено количество запросов. Ждем указанное время...")
            time.sleep(15 * 60)
        data = response.json().get('items', [])
        if not data:
            break
        else:
            for item in data:
                items.append(item)
        page += 1
    return items


def collect_login_pass(
        category_id: int,
        show: str,
        country_code: list = None,
        spam: str = 'nomatter',
        origin: list = None,
        write_to_file: bool = False
):
    items = get_my_accounts(category_id, show, origin, spam, country_code, 'pdate_to_up')
    data = {}
    for item in items:
        data[item['item_id']] = {
            'log_data': f'{item["loginData"]["login"]}:{item["loginData"]["password"]}',
            'country_code': item['telegram_country']
        }
        if item["is_sticky"] == 1:
            market.managing.unstick(item['item_id'])
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    if write_to_file:
        write_json(data, f'{today}_accounts_data.json')
    print(f"Собрано {len(data)} аккаунтов")
    return data


def delete_accounts(accounts=None, path=False, debug=False):
    if path:
        data = read_json(path)
    else:
        data = accounts
    if not data:
        raise Exception("You not specified data")
    for account_id in data.keys():
        del_status = delete_item(account_id)
        if debug:
            print(del_status)
    print(f"С маркета удалено {len(data)} аккаунтов")
    return True


def upload_items(
        category_id: Literal[
            "1", "3", "4", "5", "6", "7", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "22", "24", "27", "28", "30", "31"],
        origin: Literal["brute", "stealer", "phishing", "autoreg", "personal", "resale", "dummy", "self_registration"],
        currency: Literal["rub", "uah", "kzt", "byn", "usd", "eur", "gbp", "cny", "try", "jpy", "brl"] = "usd",
        price: float = None,
        guarantee: Literal["-1", "0", "1"] = None,
        accounts: dict = None,
        accounts_path: str = None,
        single_acc_info: dict = None,
        single_acc_id: str = None,
        title: str = None,
        title_en: str = None,
        description: str = None,
        information: str = None,
        tag_id: list = None,
        email: str = None,
        email_type: Literal["native", "autoreg"] = None,
        extra: dict[Literal[
            "proxy", "close_item", "region", "service", "system", "confirmationCode", "cookies", "login_without_cookies", "cookie_login", "mfa_file", "dota2_mmr", "ea_games", "uplay_games", "the_quarry", "warframe", "ark", "ark_ascended", "genshin_currency", "honkai_currency", "zenless_currency", "telegramClient", "telegramJson", "checkChannels", "checkSpam", "checkHypixelBan"], str] = None,
        allow_ask_discount: bool = None,
        proxy_id: int = None,
        proxy_random: bool = None,
        debug: bool = False,
        delay: float = None
):
    # Источник: single или accounts/accounts_path
    if single_acc_info:
        target = {single_acc_id: single_acc_info}
    elif accounts_path:
        data = read_json(accounts_path)
        target = data
    else:
        data = accounts
        target = data
    if not target:
        raise Exception("You not specified data")
    new_ids = {} # Для возврата новых id (если несколько)
    for old_item_id, acc_info in list(target.items()):
        # Достаём страну и данные
        country_code = acc_info.get("country_code")
        if country_code == "USA": country_code = "US" # Сопоставление, если нужно
        eff_price = price if price is not None else ACCOUNT_DATA_FOR_COUNTRY.get(country_code, {}).get("price")
        eff_title = title if title is not None else ACCOUNT_DATA_FOR_COUNTRY.get(country_code, {}).get("title")
        eff_title_en = title_en if title_en is not None else ACCOUNT_DATA_FOR_COUNTRY.get(country_code, {}).get(
            "title_en")
        ld = acc_info.get("log_data")
        if not ld:
            if debug:
                print(f"Пропуск {old_item_id}: нет log_data")
            continue
        login, password = ld.split(":", 1)
        # Публикация
        resp = market.publishing.fast(
            price=eff_price,
            category_id=category_id,
            origin=origin,
            currency=currency,
            guarantee=guarantee,
            title=eff_title,
            title_en=eff_title_en,
            description=description,
            information=information,
            login=login,
            password=password,
            tag_id=tag_id,
            email=email,
            email_type=email_type,
            extra=extra,
            allow_ask_discount=allow_ask_discount,
            proxy_id=proxy_id,
            proxy_random=proxy_random
        )
        response = resp.json()
        if debug:
            print(response)
        try:
            new_item_id = response['item']['item_id']
            new_ids[old_item_id] = new_item_id
            print(f"Аккаунт {old_item_id} залит на маркет под новым id: {new_item_id}")
        except Exception:
            if debug:
                print(f"Не удалось получить new item_id для {old_item_id}")
            new_item_id = None
        if delay:
            time.sleep(delay)
    # Если single — return single new_id
    if single_acc_info:
        return new_ids.get(single_acc_id)
    print(f"Залив завершён. Новых ключей: {len(new_ids)}")
    return new_ids # Или обновить accounts, но для single не нужно


def autopost_top(args):
    # Время
    today = datetime.date.today()
    start_dt = datetime.datetime.combine(today, datetime.time.fromisoformat(args.start_time))
    end_dt = datetime.datetime.combine(today, datetime.time.fromisoformat(args.end_time)) if args.end_time else None
    delay_sec = args.base_delay * 60
    origin = 'autoreg'
    filter_country = ["US", "CY", "TR"]
    spam_filter = "no"
    extra = {"checkChannels": True, "checkSpam": True}
    debug = False

    try:
        # Чтение удалённых, но не перезалитых аккаунтов
        deleted_items = []
        if os.path.exists(DELETED_ITEMS_PATH):
            try:
                deleted_items = read_json(DELETED_ITEMS_PATH)
                print(f"Загружено {len(deleted_items)} удалённых аккаунтов из {DELETED_ITEMS_PATH}")
            except Exception as e:
                print(f"Ошибка чтения {DELETED_ITEMS_PATH}: {e}")

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

        # Проверка и заливка ранее удалённых, но не перезалитых
        current_ids = set(accounts_data.keys())
        remaining_to_upload = [(item_id, acc_info) for item_id, acc_info in deleted_items if item_id not in current_ids]
        if remaining_to_upload:
            print(f"Заливаем {len(remaining_to_upload)} ранее удалённых аккаунтов...")
            sticky_deque = deque(maxlen=3)
            for old_item_id, acc_info in remaining_to_upload:
                new_item_id = upload_items(
                    category_id=args.category_id,
                    origin=origin,
                    single_acc_id=old_item_id,
                    single_acc_info=acc_info,
                    description=DESCRIPTION,
                    extra=extra,
                    debug=debug,
                    delay=0
                )
                if new_item_id:
                    accounts_data[new_item_id] = acc_info
                    try:
                        if len(sticky_deque) >= 3:
                            old_sticky = sticky_deque[0]
                            market.managing.unstick(old_sticky)
                        market.managing.stick(new_item_id)
                        sticky_deque.append(new_item_id)
                    except Exception as e:
                        print(f"Ошибка sticky для {new_item_id}: {e}")
            # Очищаем deleted_items.json после заливки
            write_json([], DELETED_ITEMS_PATH)

        # Queue для ротации (oldest first)
        queue = deque(accounts_data.items())
        sticky_deque = deque(maxlen=3)

        now = datetime.datetime.now()
        if now < start_dt:
            wait_sec = (start_dt - now).total_seconds()
            print(f"Ожидание {wait_sec / 60:.1f} минут…")
            time.sleep(wait_sec)

        print("Начинаем ротацию аккаунтов...")
        deleted_items = []

        while (args.infinite_loop or (end_dt and datetime.datetime.now() < end_dt)) and queue:
            old_item_id, acc_info = queue.popleft()
            del_resp = delete_item(old_item_id)
            if 'error' in del_resp:
                print(f"Аккаунт {old_item_id} уже недоступен (продан?), пропуск.")
                continue

            # Добавляем в список удалённых и сохраняем в файл
            deleted_items.append((old_item_id, acc_info))
            write_json(deleted_items, DELETED_ITEMS_PATH)

            new_item_id = upload_items(
                category_id=args.category_id,
                origin=origin,
                single_acc_id=old_item_id,
                single_acc_info=acc_info,
                description=DESCRIPTION,
                extra=extra,
                debug=debug,
                delay=0
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

    finally:
        # Финальная заливка всех удалённых, но не перезалитых
        current_queue_ids = {item_id for item_id, _ in queue}
        remaining_to_upload = [(item_id, acc_info) for item_id, acc_info in deleted_items if item_id not in current_queue_ids]
        if remaining_to_upload:
            print(f"Финальная заливка {len(remaining_to_upload)} удалённых аккаунтов...")
            for old_item_id, acc_info in remaining_to_upload:
                new_item_id = upload_items(
                    category_id=args.category_id,
                    origin=origin,
                    single_acc_id=old_item_id,  # передаём настоящий id
                    single_acc_info=acc_info,
                    description=DESCRIPTION,
                    extra=extra,
                    debug=debug,
                    delay=0
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
        write_json([], DELETED_ITEMS_PATH)
        print("Ротация и финальная заливка завершены.")


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
