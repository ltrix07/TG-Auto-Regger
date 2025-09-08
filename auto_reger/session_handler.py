from telethon.errors import FloodError, PasswordHashInvalidError, SessionPasswordNeededError
from utils import read_txt_list
from auto_reger.session_converter import Converter
import random


API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'
TELEGRAM_CLIENT = {
    "telegram_device_model": "Aspire A715-42G",
    "telegram_system_version": "Windows 10 x64",
    "telegram_app_version": "6.1.2 x64"
}


def set_2fa_safe(auth_key, dc_id, country, password, cur_password=None, hint="my password"):
    proxy_list = read_txt_list(f'{country}_proxies.txt')
    proxy_str_splat = random.choice(proxy_list).split(':')
    proxy = (
        'socks5',
        proxy_str_splat[0],
        proxy_str_splat[1],
        True,
        proxy_str_splat[2],
        proxy_str_splat[3]
    )
    converter = Converter('./')
    client = converter.define_client_from_auth_key(
        auth_key_hex=auth_key,
        dc_id=dc_id,
        api_id=API_ID,
        api_hash=API_HASH,
        system_version=TELEGRAM_CLIENT['telegram_system_version'],
        device_model=TELEGRAM_CLIENT['telegram_device_model'],
        app_version=TELEGRAM_CLIENT['telegram_app_version'],
        proxy=proxy
    )
    try:
        result = client.edit_2fa(
            current_password=cur_password,
            new_password=password,
            hint=hint
        )
        if password:
            print("✅ Cloud Password set successfully:", result)
        else:
            print("✅ Cloud Password reset successfully:", result)

    except FloodError as e:
        if hasattr(e, "seconds") and e.seconds:
            print(f"⏳ FloodError: нельзя менять пароль сейчас. Подожди {e.seconds} секунд (~{round(e.seconds/3600, 2)} ч).")
        else:
            print("⏳ FloodError: метод заморожен. На этом аккаунте сейчас нельзя менять пароль (FROZEN_METHOD_INVALID).")

    except PasswordHashInvalidError:
        print("❌ Неверный текущий пароль (cur_password).")

    except SessionPasswordNeededError:
        print("⚠️ На аккаунте уже стоит пароль, нужно передавать cur_password.")

    except Exception as e:
        print("⚠️ Другая ошибка:", repr(e))


if __name__ == '__main__':
    set_2fa_safe(
        r'C:\Users\Владимир\PycharmProjects\TG-Auto-Reg\auto_reger\sessions\test.session',
        'USA',
        None,
        'TestPass123'
    )
