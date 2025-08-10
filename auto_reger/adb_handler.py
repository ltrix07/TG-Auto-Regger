import random
import logging
import subprocess
import secrets
import time
import string
import base64
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import NameOID
from datetime import datetime, timedelta


logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    encoding='utf-8')

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.127 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.93 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/68.0 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/69.0 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/70.0 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/71.0 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/72.0 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/12.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/12.1 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/13.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Edge/44.0.2403.119 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Edge/45.0.2454.94 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Edge/46.0.2486.0 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Opera/58.0.3135.107 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Opera/59.0.3206.125 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Opera/60.0.3255.109 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) UCBrowser/13.2.0.1298 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) UCBrowser/13.3.0.1305 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.101 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.181 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/73.0 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/74.0 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/75.0 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/13.2 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/14.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Edge/44.0.2403.140 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Edge/45.0.2454.62 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Opera/61.0.3290.111 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Opera/62.0.3331.99 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) UCBrowser/13.4.0.1306 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.62 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/76.0 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/77.0 Mobile"
]


DEVICE_NAMES = [
    "SM-G991U",   # Samsung Galaxy S21 5G (для США)
    "SM-G988B",   # Samsung Galaxy S20 Ultra (международная версия)
    "SM-A525F",   # Samsung Galaxy A52 (международная версия)
    "SM-A716U",   # Samsung Galaxy A71 5G (для США)
    "SM-N986B",   # Samsung Galaxy Note20 Ultra 5G (международная версия)
    "SM-S908E",   # Samsung Galaxy S22 Ultra (международная версия)
    "SM-F711B",   # Samsung Galaxy Z Flip3 5G (международная версия)
    "SM-X205",    # Samsung Galaxy Tab A8 10.5 (планшет)
    "SM-M315F",   # Samsung Galaxy M31 (международная версия)
    "SM-A125F",   # Samsung Galaxy A12 (международная версия)
    "SM-G973F",   # Samsung Galaxy S10 (международная версия)
    "SM-G781B",   # Samsung Galaxy S20 FE 5G (международная версия)
    "SM-T225",    # Samsung Galaxy Tab A7 Lite (планшет)
]


def run_adb_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Ошибка ADB: {e.stderr}")
        raise


def connect_adb(udid, max_attempts=3):
    adb_path = r"C:\Android\platform-tools\adb.exe"
    for attempt in range(1, max_attempts + 1):
        print(f"Attempt {attempt}/{max_attempts} to connect to {udid}")
        adb_command = f'"{adb_path}" connect {udid}'
        process = subprocess.Popen(adb_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        if error:
            print(f"Error connecting to ADB for {udid}: {error.decode()}")
        else:
            print(f"ADB connected to {udid}: {output.decode()}")
            adb_command = f'"{adb_path}" -s {udid} shell echo online'
            process = subprocess.Popen(adb_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output, error = process.communicate()
            if not error and "online" in output.decode().strip():
                return True
        time.sleep(2)
    print(f"Failed to connect to {udid} after {max_attempts} attempts")
    return False


def generate_number(nqty):
    number = ''
    for _ in range(nqty):
        number += str(random.randint(0, 9))

    return number


def get_device_info(udid):
    adb_path = r"C:\Android\platform-tools\adb.exe"
    # Версия Android
    process = subprocess.Popen(f'"{adb_path}" -s {udid} shell getprop ro.build.version.release', stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    android_version = output.decode().strip() if not error else "Unknown"

    process = subprocess.Popen(f'"{adb_path}" -s {udid} shell getprop ro.product.model', stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    device_model = output.decode().strip() if not error else "Unknown"

    process = subprocess.Popen(f'"{adb_path}" -s {udid} shell dumpsys package org.telegram.messenger.web | grep versionName', stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    tg_version = output.decode().strip().replace('versionName=', '') if not error else "Unknown"

    process = subprocess.Popen(
        f'"{adb_path}" -s {udid} shell getprop persist.sys.locale',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    sys_lang = output.decode().strip() if not error else "Unknown"

    # API Level
    process = subprocess.Popen(f'"{adb_path}" -s {udid} shell getprop ro.build.version.sdk', stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    api_level = output.decode().strip() if not error else "Unknown"

    # ABI
    process = subprocess.Popen(f'"{adb_path}" -s {udid} shell getprop ro.product.cpu.abi', stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    abi = output.decode().strip() if not error else "Unknown"

    print(f"Device Info: Android Version={android_version}, API Level={api_level}, ABI={abi}, Device Model={device_model} "
          f"Telegram Version={tg_version}, System language={sys_lang}")
    return {
        'model': device_model,
        'android': android_version,
        'tg': tg_version,
        'sys_lang': sys_lang
    }


def generate_random_imei():
    imei = "35" + "".join([str(random.randint(0, 9)) for _ in range(12)])
    digits = [int(d) for d in imei]
    doubled = [2 * d if i % 2 else d for i, d in enumerate(digits)]
    summed = sum(d if d < 10 else d - 9 for d in doubled)
    luhn = (10 - summed % 10) % 10
    return imei + str(luhn)


def change_imei():
    try:
        new_imei = generate_random_imei()
        logging.info(f"Generated IMEI: {new_imei}")

        # Установка нового IMEI
        process = subprocess.Popen(
            'adb shell',
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )

        # Отправляем команды построчно
        commands = [
            'su',
            f'setprop persist.radio.imei {new_imei}',
            'exit',
            'exit'
        ]

        try:
            stdout, stderr = process.communicate('\n'.join(commands), timeout=10)
            if stderr:
                print(f"Ошибка смены IMEI: {stderr}")
                raise subprocess.CalledProcessError(process.returncode, commands, stderr=stderr)

            print(f'New IMEI generated: {new_imei}')
        except subprocess.TimeoutExpired as e:
            print(f"Ошибка смены IMEI: {e}")
            process.kill()
            raise
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to change IMEI: {e.stderr}")
        raise RuntimeError(f"Failed to change IMEI: {e.stderr}")


def generate_android_id(nbytes=8):
    try:
        return secrets.token_hex(nbytes)
    except Exception as e:
        logging.error(f"Error generating/setting Android ID: {str(e)}")
        return None


def generate_android_build_id_past():
    # Ветка разработки для Android 9.
    build_branch = "PQ3B"

    # Текущая дата
    today = datetime.today()

    # Генерируем случайное количество дней в диапазоне от 365 до 730 (примерно 1-2 года)
    days_ago = random.randint(365, 730)

    # Вычисляем рандомизированную дату в прошлом
    past_date = today - timedelta(days=days_ago)

    # Форматируем дату в строку ГГММДД
    formatted_date = past_date.strftime("%y%m%d")

    # Генерируем уникальный 8-значный идентификатор
    unique_id = ''.join(random.choices(string.digits, k=8))

    # Собираем все части в одну строку
    build_id = f"{build_branch}.{formatted_date}.{unique_id}"

    return build_id


def generate_and_set_user_agent():
    """
    Генерирует случайный User-Agent для встроенного браузера и устанавливает его.
    Возвращает новый User-Agent или None в случае ошибки.
    """
    try:
        new_user_agent = random.choice(USER_AGENTS)
        process = subprocess.Popen(
            "adb shell",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        commands = [
            "su",
            f"settings put global http_user_agent \"{new_user_agent}\"",
            "exit",
            "exit"
        ]
        stdout, stderr = process.communicate("\n".join(commands), timeout=10)
        if stderr:
            logging.error(f"Failed to set User-Agent with su: {stderr}")
            return None
        logging.info(f"User-Agent changed to {new_user_agent}")
        return new_user_agent
    except Exception as e:
        logging.error(f"Error setting User-Agent: {str(e)}")
        return None


def change_setting(level, setting_name, value):
    try:
        process = subprocess.Popen(
            "adb shell",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        commands = [
            "su",
            f"settings put {level} {setting_name} {value}",
            "exit",
            "exit"
        ]
        stdout, stderr = process.communicate("\n".join(commands), timeout=10)
        if stderr:
            logging.error(f"Failed to set property {setting_name} id with su: {stderr}")
            return None
        logging.info(f"Setting {setting_name} changed to {value}")
    except Exception as e:
        logging.error(f"Error setting Device ID: {str(e)}")
        return None


def change_prop(setting_name, value):
    try:
        process = subprocess.Popen(
            "adb shell",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        commands = [
            "su",
            f"setprop {setting_name} {value}",
            "exit",
            "exit"
        ]
        stdout, stderr = process.communicate("\n".join(commands), timeout=10)
        if stderr:
            logging.error(f"Failed to set property {setting_name} id with su: {stderr}")
            return None
        logging.info(f"Setting {setting_name} changed to {value}")
    except Exception as e:
        logging.error(f"Error setting Device ID: {str(e)}")
        return None


def set_random_timezone():
    try:
        timezones = ["America/New_York", "America/Los_Angeles", "America/Chicago"]
        new_timezone = random.choice(timezones)
        process = subprocess.Popen(
            "adb shell",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        commands = [
            "su",
            f"setprop persist.sys.timezone {new_timezone}",
            "exit",
            "exit"
        ]
        stdout, stderr = process.communicate("\n".join(commands), timeout=10)
        if stderr:
            logging.error(f"Failed to set new timezone with su: {stderr}")
            return None
        logging.info(f"Timezone changed to {new_timezone}")
        return new_timezone
    except Exception as e:
        logging.error(f"Error setting timezone: {str(e)}")
        return None


def compare_emulator_settings(udid1, udid2, adb_path=r"C:\Android\platform-tools\adb.exe"):
    """
    Сравнивает настройки prop, secure, global, system между двумя эмуляторами.
    Выводит свойства, которые различаются.
    :param udid1: UDID первого эмулятора
    :param udid2: UDID второго эмулятора
    :param adb_path: Путь к ADB
    :return: Словарь с различающимися настройками
    """

    def get_settings(udid, namespace):
        """Получает настройки для указанного namespace (secure, global, system)"""
        command = f'"{adb_path}" -s {udid} shell settings list {namespace}'
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        if error:
            logging.error(f"Ошибка при получении настроек {namespace} для {udid}: {error.decode()}")
            return {}

        settings = {}
        for line in output.decode().splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                settings[key.strip()] = value.strip()
        return settings

    def get_default_props(udid):
        """Получает свойства default через getprop"""
        command = f'"{adb_path}" -s {udid} shell getprop'
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        if error:
            logging.error(f"Ошибка при получении default props для {udid}: {error.decode()}")
            return {}

        props = {}
        for line in output.decode().splitlines():
            if line.startswith('[') and ']: [' in line:
                key = line.split(']: [')[0].strip('[').strip()
                value = line.split(']: [')[1].strip(']')
                props[key] = value
        return props

    try:
        # Проверка подключения к обоим эмуляторам
        if not connect_adb(udid1) or not connect_adb(udid2):
            logging.error(f"Не удалось подключиться к одному из эмуляторов: {udid1}, {udid2}")
            return {}

        # Получение настроек для обоих эмуляторов
        settings_types = ['default', 'secure', 'global', 'system']
        emulator1_settings = {}
        emulator2_settings = {}

        for stype in settings_types:
            if stype == 'default':
                emulator1_settings[stype] = get_default_props(udid1)
                emulator2_settings[stype] = get_default_props(udid2)
            else:
                emulator1_settings[stype] = get_settings(udid1, stype)
                emulator2_settings[stype] = get_settings(udid2, stype)

        # Сравнение настроек
        differences = {}
        for stype in settings_types:
            differences[stype] = {}
            # Получить все ключи из обоих эмуляторов
            all_keys = set(emulator1_settings[stype].keys()) | set(emulator2_settings[stype].keys())
            for key in all_keys:
                value1 = emulator1_settings[stype].get(key, "Отсутствует")
                value2 = emulator2_settings[stype].get(key, "Отсутствует")
                if value1 != value2:
                    differences[stype][key] = {
                        f"{udid1}": value1,
                        f"{udid2}": value2
                    }

        # Вывод различий
        print(f"\nРазличия в настройках между эмуляторами {udid1} и {udid2}:")
        for stype in differences:
            if differences[stype]:
                print(f"\nТип настроек: {stype}")
                for key, values in differences[stype].items():
                    print(f"  Ключ: {key}")
                    print(f"    {udid1}: {values[udid1]}")
                    print(f"    {udid2}: {values[udid2]}")

        # Логирование различий
        logging.info(
            f"Сравнение настроек для {udid1} и {udid2} завершено. Найдено различий: {sum(len(d) for d in differences.values())}")
        return differences

    except Exception as e:
        logging.error(f"Ошибка при сравнении настроек: {e}")
        return {}


def generate_stable_secret():
    groups = [''.join(random.choices(string.hexdigits.lower(), k=4)) for _ in range(8)]
    return ':'.join(groups)


def generate_mac_address():
    # Создаем список из 6 случайных шестнадцатеричных чисел (0-255)
    mac_parts = [random.randint(0x00, 0xFF) for _ in range(6)]

    # Форматируем каждое число в двухзначный шестнадцатеричный формат с ведущими нулями
    # и объединяем их через двоеточие. Используем 'X' для заглавных букв.
    mac_address = ":".join(f"{part:02X}" for part in mac_parts)

    return mac_address


def generate_x509_token():
    try:
        # Генерация приватного ключа
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        # Создание имени субъекта
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Mountain View"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Google Inc"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Android"),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, "security@android.com"),
        ])

        # Создание сертификата
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=30))
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName("android.com")]),
                critical=False
            )
            .sign(private_key, hashes.SHA256())
        )

        # Кодирование сертификата в Base64
        cert_bytes = cert.public_bytes(Encoding.DER)
        base64_token = base64.b64encode(cert_bytes).decode('utf-8')

        logging.info("Сгенерирован новый X.509 токен")
        return base64_token
    except Exception as e:
        logging.error(f"Ошибка при генерации X.509 токена: {e}")
        return None


def reset_telegram_data(udid):
    try:
        # Перевірка підключених пристроїв
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        if "device" not in result.stdout:
            logging.error("No devices found. Ensure USB Debugging is enabled and device is connected.")
            return False

        # Якщо вказано UDID, використовуємо його
        adb_prefix = ["adb", "-s", udid] if udid else ["adb"]

        # Закриття Telegram
        subprocess.run(adb_prefix + ["shell", "am", "force-stop", "org.telegram.messenger"], check=True)
        logging.info("Telegram app closed successfully")

        # Очищення даних Telegram
        subprocess.run(adb_prefix + ["shell", "pm", "clear", "org.telegram.messenger"], check=True)
        logging.info("Telegram data cleared successfully")

        # Скидання Advertising ID
        subprocess.run(adb_prefix + ["shell", "settings", "delete", "secure", "advertising_id"], check=True)
        logging.info("Advertising ID reset successfully")

        new_android_id = generate_android_id()
        new_device_id = generate_android_id()
        new_cert = generate_x509_token()
        new_build_id = generate_android_build_id_past()
        new_mac = generate_mac_address()

        # new_device_name = random.choice(DEVICE_NAMES)
        new_bluetooth_address = ':'.join(['{:02x}'.format(random.randint(0, 255)) for _ in range(6)])

        generate_and_set_user_agent()
        change_setting('secure', 'android_id', new_android_id)
        change_setting('secure', 'android_id', '$(cat /proc/sys/kernel/random/uuid)')
        change_setting('secure', 'bluetooth_address', new_bluetooth_address)
        # change_setting('secure', 'bluetooth_name', new_device_name)
        change_setting('secure', 'device_id', new_device_id)
        change_setting('secure', 'config_update_certificate', new_cert)
#         change_setting('secure', 'device_name', new_device_name)
        change_setting('global', 'database_creation_buildid', new_build_id)
#         change_setting('global', 'device_name', new_device_name)
        change_prop('ro.product.cpu.abi', random.choice(['arm64-v8a', 'armeabi-v7a']))
        change_prop('wifi.interface.mac', new_mac)
        change_prop('ro.boottime.zygote_secondary', generate_number(10))
        change_prop('ro.boottime.vendor.bluetooth-1-0', generate_number(10))
        change_prop('ro.boottime.console', generate_number(10))
        change_prop('ro.boottime.vendor.ril-daemon', generate_number(10))
        change_prop('ro.boottime.traced', generate_number(10))
        change_prop('ro.boottime.cameraserver', generate_number(10))
        change_prop('ro.boottime.hidl_memory', generate_number(10))
#         change_prop('ro.product.model', new_device_name)
        change_prop('ro.boottime.ueventd', generate_number(10))
        change_prop('ro.boottime.vendor.gnss_service', generate_number(10))
        change_prop('ro.boottime.vendor.audio-hal-2-0', generate_number(10))
        change_prop('ro.boottime.usbd', generate_number(10))
        change_prop('ro.boottime.vendor.health-hal-2-0', generate_number(10))
        change_prop('ro.boottime.tombstoned', generate_number(10))
        change_prop('ro.boottime.hwservicemanager', generate_number(10))
        change_prop('ro.boottime.vendor.wifi_hal_legacy', generate_number(10))
        change_prop('ro.boottime.keystore', generate_number(10))
        change_prop('ro.boottime.vendor.power-hal-1-1', generate_number(10))
        change_prop('ro.boottime.mediametrics', generate_number(10))
        change_prop('ro.boottime.surfaceflinger', generate_number(10))
        change_prop('persist.netd.stable_secret', generate_stable_secret())
#         change_prop('ro.product.board', new_device_name)
        change_prop('ro.boottime.init', generate_number(4))
        change_prop('ro.boottime.init.selinux', generate_number(2))
#         change_prop('ro.product.name', new_device_name)
        set_random_timezone()
        change_imei()

        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to reset Telegram data: {e}")
        return False
    except Exception as e:
        logging.error(f"Error during Telegram data reset: {e}")
        return False


if __name__ == '__main__':
    change_prop('ro.product.cpu.abi', random.choice(['arm64-v8a', 'armeabi-v7a']))
