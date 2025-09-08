import time
from LOLZTEAM.Client import Market
from auto_reger.utils import write_json, read_json
from datetime import datetime
from typing import Literal


DESCRIPTION = """Бонус за отзыв:

Оставьте отзыв о покупке и получите скидку 10% на следующую покупку! 1 отзыв = 1 скидка. Для оптовых заказов пишите в ЛС — обсудим индивидуальные условия!

 Гарантия:

•  3 дня гарантии при условии, что аккаунт не используется для спама или действий, нарушающих правила Telegram.

•  В случае проблем — оперативная поддержка.

 Важно:

В первую неделю использования обязательно подключайтесь через прокси страны регистрации аккаунта для стабильной работы.

Пишите в ЛС для заказа, уточнения деталей или оптовых предложений!

Надежность, качество, поддержка — ваш успех с нашими аккаунтами!"""

ACCOUNT_DATA_FOR_COUNTRY = {
    "USA": {"title": "+1 - США | НОВЫЙ АККАУНТ | ВХОД С ЛЮБОГО УСТРОЙСТВА",
           "title_en": "+1 - USA | New account | Entrance from any device", "price": 0.93, "country_code": "UA"},
    "Cyprus": {"title": "+357 КИПР | НОВЫЙ АККАУНТ | ВХОД С ЛЮБОГО УСТРОЙСТВА",
           "title_en": "+357 Cyprus | New account | Entrance from any device", "price": 4, "country_code": "CY"},
    "Turkey": {"title": "+90 ТУРЦИЯ | НОВЫЙ АККАУНТ | ВХОД С ЛЮБОГО УСТРОЙСТВА",
           "title_en": "+90 Türkiye | New account | Entrance from any device", "price": 3.5, "country_code": "TR"},
    "Poland": {"title": "+48 ПОЛЬША | НОВЫЙ АККАУНТ | ВХОД С ЛЮБОГО УСТРОЙСТВА",
           "title_en": "+48 Poland | New account | Entrance from any device", "price": 2.4, "country_code": "PL"},
    "Ukraine": {"title": "+380 УКРАИНА | НОВЫЙ АККАУНТ | ВХОД С ЛЮБОГО УСТРОЙСТВА",
                "title_en": "+380 UKRAINE | New account | Entrance from any device", "price": 8, "country_code": "UA"}
}
TELEGRAM_CLIENT = {
    "telegram_device_model": "Aspire A715-42G",
    "telegram_system_version": "Windows 10 x64",
    "telegram_app_version": "6.1.2 x64"
}
TOKEN_PATH = r'C:\Users\Владимир\PycharmProjects\TG-Auto-Reg\lzt_token.txt'
with open(TOKEN_PATH, 'rb') as file:
    TOKEN = bytes.decode(file.read())
market = Market(TOKEN)


def delete_item(item_id, reason='test'):
    response = market.managing.delete(item_id, reason)
    if response.status_code == 200:
        delete_from_trash = market.managing.delete(item_id, reason)
        return delete_from_trash.json()
    return response.json()


def get_my_accounts(category_id: int, show: str, origin: list, spam: str, country_code: list = None, order_by=None):
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

    today = datetime.now().strftime('%Y-%m-%d')
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
        accounts: dict = None,  # полный набор (опционально)
        accounts_path: str = None,  # путь к файлу (опционально)
        single_acc_info: dict = None,  # для заливки одного аккаунта (опционально)
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
        target = {"temp_id": single_acc_info}  # Временный dict для одного
    elif accounts_path:
        data = read_json(accounts_path)
        target = data
    else:
        data = accounts
        target = data

    if not target:
        raise Exception("You not specified data")

    new_ids = {}  # Для возврата новых id (если несколько)

    for old_item_id, acc_info in list(target.items()):
        # Достаём страну и данные
        country_code = acc_info.get("country_code")
        if country_code == "USA": country_code = "US"  # Сопоставление, если нужно
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
        return new_ids.get("temp_id")

    print(f"Залив завершён. Новых ключей: {len(new_ids)}")
    return new_ids  # Или обновить accounts, но для single не нужно