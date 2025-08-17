import subprocess
import psutil
import time
import os
import random
import logging
import socks
import asyncio
import aiohttp
import shutil
from datetime import datetime
from auto_reger.adb_handler import reset_telegram_data, run_adb_command, get_device_info
from auto_reger.session_converter import transfer_dat_session, convert_dat_to_session
from telethon import TelegramClient
from auto_reger.utils import read_json, write_json
from auto_reger.sms_api import SmsApi, remove_activation_from_json, save_activation_to_json, can_set_status_8
from auto_reger.emulator_handler import Telegram
from auto_reger.app_handler import Onion, VPN, TelegramDesktop
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from concurrent.futures import ThreadPoolExecutor

# Настройка кодировки для корректного вывода
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Настройка логирования
logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

CECH_PATH = './cech.json'
SESSIONS_DIR = './sessions/JSON'
MAX_THREADS = 5
SMS_TIMEOUT = 120
COUNTRY = input('Enter country for registration Telegram account (USA, United Kingdom, etc.): ').strip()
MAX_PRICE = float(input('Enter maximum price: ').strip())


def setup_cech():
    if os.path.isfile(CECH_PATH):
        return read_json(CECH_PATH)
    cech_data = {}
    write_json(cech_data, CECH_PATH)
    return cech_data


def load_names(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def perform_neutral_actions(client):
    try:
        # Получение списка диалогов для имитации активности
        result = client(GetDialogsRequest(
            offset_date=None,
            offset_id=0,
            offset_peer=None,
            limit=10,
            hash=0
        ))
        logging.info("Neutral action: Retrieved dialogs")
        time.sleep(random.uniform(2, 5))
    except Exception as e:
        logging.error(f"Failed neutral actions: {str(e)}")


def save_session(phone_number, first_name, last_name, email_log, email_pass, activation_cost,
                 device_model, android_v, tg_v, system_lang):
    session_data = {
        'phone_number': phone_number,
        'first_name': first_name,
        'last_name': last_name,
        'email_login': email_log,
        'email_password': email_pass,
        'activation_cost': activation_cost,
        'device_model': device_model,
        'android': android_v,
        'telegram_version': tg_v,
        'system_lang': system_lang
    }
    session_file = os.path.join(SESSIONS_DIR, f"{phone_number}.json")
    write_json(session_data, session_file)
    logging.info(f"Session saved for {phone_number} at {session_file}")


def generate_random_string(length=8):
    import string
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))


def is_process_running(process_name):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'].lower() == process_name.lower():
            return True
    return False


def kill_emulator(app_name):
    if is_process_running(app_name):
        subprocess.run(f"taskkill /IM {app_name} /F", shell=True, capture_output=True)
        time.sleep(2)
        logging.info(f"Emulator {app_name} terminated")
    else:
        logging.info(f"Emulator {app_name} is not running, no need to terminate")


def activation_admin(api):
    try:
        ids = [row['activation_id'] for row in read_json('activations.json') if 'activation_id' in row]
        for id_ in ids:
            if can_set_status_8(id_):
                if api.setStatus(id_, status=8):
                    remove_activation_from_json(id_)
                    logging.info(f"Set status 8 for activation_id {id_}")
                else:
                    logging.warning(f"Failed to set status 8 for activation_id {id_}")
    except Exception as e:
        logging.error(f"Error in activation_admin: {str(e)}")


def create_tdata_with_telegram_desktop(telegram: Telegram, phone_number):
    sessions_dir = os.path.join(os.path.dirname(__file__), 'sessions')

    # Путь для конвертированных TData
    today = datetime.now().strftime('%Y-%m-%d')
    converted_base_dir = os.path.join(sessions_dir, 'converted', today)
    os.makedirs(converted_base_dir, exist_ok=True)

    # Папка для конкретного аккаунта
    account_dir = os.path.join(converted_base_dir, f'acc_{phone_number}')
    os.makedirs(account_dir, exist_ok=True)

    tg_app_path = os.path.join(account_dir, 'Telegram.exe')
    shutil.copy(os.path.join(os.path.dirname(__file__), 'Telegram.exe'), tg_app_path)

    tg_desk = TelegramDesktop(tg_app_path)
    tg_desk.start_and_enter_number(phone_number)
    time.sleep(5)
    code = telegram.read_sms_with_code()
    tg_desk.enter_code(code)
    time.sleep(3)
    tg_desk.close()

    os.system(f"taskkill /F /IM Telegram.exe")
    os.remove(tg_app_path)


async def create_session_with_telethon(phone_number,
                                       telegram: Telegram,
                                       device_model,
                                       system_version,
                                       app_version,
                                       sys_lng_code,
                                       lng_code,
                                       api_id=6,
                                       api_hash='eb06d4abfb49dc3eeb1aeb98ae0f581e'):
    try:
        # Преобразование phone_number в строку и добавление "+" для международного формата
        phone_number = str(phone_number)
        if not phone_number.startswith('+'):
            phone_number = f'+{phone_number}'
        logging.info(f"Processing phone number: {phone_number}")

        # Формирование пути для файла сессии
        today = datetime.now().strftime('%Y-%m-%d')
        converted_folder = os.path.join(os.path.dirname(__file__), 'sessions', 'converted', today)
        os.makedirs(converted_folder, exist_ok=True)
        session_file_name = f'acc_{phone_number.lstrip("+")}.session'
        session_path = os.path.join(converted_folder, session_file_name)

        # Создание клиента Telethon
        client = TelegramClient(session=session_path, api_id=api_id, api_hash=api_hash,
                                device_model=device_model, system_version=system_version,
                                app_version=app_version, system_lang_code=sys_lng_code,
                                lang_code=lng_code)
        await client.connect()

        # Запрос кода
        await client.send_code_request(phone_number)
        logging.info(f"Code requested for {phone_number}")

        code = telegram.read_sms_with_code()
        if code:
            try:
                await client.sign_in(phone_number, code)
                logging.info(f"Telethon session created for {phone_number}")
                return client, session_path, None
            except SessionPasswordNeededError:
                logging.error("Two-factor authentication required, not supported")
                return None, session_path, "Two-factor authentication required"
            except PhoneCodeInvalidError:
                logging.error("Invalid Telegram code")
                return None, session_path, "Invalid code"
            finally:
                await client.disconnect()

        return None, None, None

    except Exception as e:
        logging.error(f"Telethon session creation failed for {phone_number}: {str(e)}")
        return None, None, str(e)


def phone_number_send(emulator_obj: Telegram, sms_obj: SmsApi, not_code=False):
    attempt = 0
    status = None
    activation_id = None
    number_price = None
    phone_number = None
    new_number = True

    while True:
        try:
            if not_code:
                if emulator_obj.check_element(By.XPATH, '//android.widget.TextView[@text="Didn\'t get the code?"]', timeout=2):
                    emulator_obj.click_element(By.XPATH, '//android.widget.TextView[@text="Didn\'t get the code?"]')
                    if emulator_obj.check_element(By.XPATH, '//android.widget.TextView[@text="Edit number"]', timeout=2):
                        emulator_obj.click_element(By.XPATH, '//android.widget.TextView[@text="Edit number"]')

                if emulator_obj.check_element(By.XPATH, '//android.widget.ImageView[@content-desc="Back"]', timeout=1):
                    emulator_obj.click_element(By.XPATH, '//android.widget.ImageView[@content-desc="Back"]', timeout=1)

                    if emulator_obj.check_element(By.XPATH, '//android.widget.TextView[@text="Edit"]', timeout=2):
                        emulator_obj.click_element(By.XPATH, '//android.widget.TextView[@text="Edit"]', 1)
                not_code = False

            if new_number:
                max_price = None
                if 'grizzly' not in sms_obj.api_url:
                    max_price = MAX_PRICE
                num_data = sms_obj.verification_number('tg', COUNTRY, max_price)
                print(num_data)
                phone_number = num_data.get('phoneNumber')
                activation_id = num_data.get('activationId')
                number_price = num_data.get('activationCost')

                if not phone_number:
                    if num_data['error']:
                        logging.error(f"Нет номеров. Переходим к следующей попытке...")
                        continue
                    else:
                        logging.error(f"SMS API response: {num_data}")
                logging.info(f"Попытка {attempt + 1} - Получен номер: {phone_number}")
                save_activation_to_json(activation_id, phone_number)

            if status == 'reset':
                emulator_obj.start()
                emulator_obj.click_start_messaging()
                new_number = True
                status = None

            emulator_obj.send_number(phone_number)
            time.sleep(random.uniform(1, 2))

            if emulator_obj.wait_for_element_to_disappear(By.XPATH, emulator_obj.COUNTRY_CODE_INPUT, timeout=180):
                if emulator_obj.check_element(By.XPATH, '//android.widget.TextView[@text="Check your Telegram messages"]', timeout=1) or \
                        emulator_obj.check_element(By.XPATH, emulator_obj.CHECK_EMAIL_TEXT, timeout=1):
                    logging.info(f"Номер {phone_number} уже зарегистрирован в Telegram")
                    activation_admin(sms_obj)
                    not_code = True
                    attempt += 1
                    continue

            if emulator_obj.check_element(By.XPATH, emulator_obj.NUMBER_IS_BANNED, timeout=1):
                logging.info(f"Номер {phone_number} заблокирован приложением")
                activation_admin(sms_obj)
                emulator_obj.click_element(By.XPATH, emulator_obj.OK_BTN)
                attempt += 1
                continue

            if emulator_obj.check_element(By.XPATH, emulator_obj.TOO_MANY_ATTEMPTS, timeout=1):
                logging.info("Слишком много попыток для этого эмулятора")
                reset_telegram_data(emulator_obj.udid)
                new_number = False
                status = 'reset'
                continue

            return activation_id, phone_number, number_price

        except (NoSuchElementException, TimeoutException) as e:
            logging.error(f"Ошибка не получается найти элемент: {str(e)}")
            attempt += 1
            time.sleep(2)
        except Exception as e:
            logging.error(f"Ошибка при попытке {attempt + 1}: {str(e)}")
            attempt += 1
            time.sleep(2)
        finally:
            activation_admin(sms_obj)


def check_2fa(telegram: Telegram, onion: Onion, sms_api: SmsApi, first_names, last_names, phone_number, activation_id):
    if telegram.check_element(By.XPATH, telegram.NAME_FIELD, timeout=5):
        first_name = random.choice(first_names) if first_names else generate_random_string(6)
        last_name = random.choice(last_names) if last_names else generate_random_string(8)
        telegram.enter_name(first_name, last_name)
        logging.info(f"Entered name: {first_name} {last_name}")
        return first_name, last_name

    if telegram.check_element(By.XPATH, telegram.PASS_NEED_TEXT, timeout=3):
        telegram.click_element(By.XPATH, telegram.FORGOT_PASS_BTN, timeout=3)
        telegram.click_element(By.XPATH, telegram.RESET_ACC_BTN, timeout=3)
        telegram.click_element(By.XPATH, telegram.RESET_ACC_BTN, timeout=3)
        time.sleep(2)

    if telegram.check_element(By.XPATH, telegram.NAME_FIELD, timeout=5):
        first_name = random.choice(first_names) if first_names else generate_random_string(6)
        last_name = random.choice(last_names) if last_names else generate_random_string(8)
        telegram.enter_name(first_name, last_name)
        logging.info(f"Entered name: {first_name} {last_name}")
    else:
        return None, None

    if telegram.check_element(By.XPATH, telegram.OK_BTN, timeout=2):
        telegram.click_element(By.XPATH, telegram.OK_BTN, timeout=2)

    if telegram.check_element(By.XPATH, telegram.DONE_BTN, timeout=2):
        telegram.click_element(By.XPATH, telegram.DONE_BTN, timeout=2)
        telegram.click_element(By.XPATH, telegram.YES_BTN, timeout=2)

    if telegram.check_element(By.XPATH, telegram.TOO_MANY_ATTEMPTS, timeout=2):
        reset_telegram_data(telegram.udid)
        telegram.start()
        telegram.click_start_messaging()
        telegram.send_number(phone_number)

    if telegram.check_element(By.XPATH, telegram.CHECK_EMAIL_TEXT, timeout=2):
        code = onion.extract_code(second_req=True)
        run_adb_command(f'input text "{code}"')

    if telegram.check_element(By.XPATH, telegram.ENTER_CODE_TEXT, timeout=2):
        sms_api.setStatus(activation_id, status=3)
        code = sms_api.check_verif_status(activation_id, SMS_TIMEOUT)
        run_adb_command(f'input text "{code}"')

    if telegram.check_element(By.XPATH, telegram.NAME_FIELD, timeout=5):
        first_name = random.choice(first_names) if first_names else generate_random_string(6)
        last_name = random.choice(last_names) if last_names else generate_random_string(8)
        telegram.enter_name(first_name, last_name)
        logging.info(f"Entered name: {first_name} {last_name}")
        return first_name, last_name
    else:
        return None, None


def register_account(device_config, sms_srvice, sms_api_key_path, first_names, last_names, index):
    telegram = None
    sms_activate = None
    activation_id = None

    try:
        is_physical = device_config.get('is_physical', False)
        if is_physical:
            udid = device_config['udid']
            telegram = Telegram(udid=udid, appium_port=device_config['appium_port'], emulator_path=None, emulator_name=None)
            logging.info(f"Using physical device with UDID: {udid} for account {index}")
        else:
            telegram = Telegram(udid=None, appium_port=device_config['appium_port'], emulator_path=device_config['app_path'], emulator_name=device_config['app_name'])
            logging.info(f"Starting emulator for account {index}")
            result = telegram.start_emulator(device_config['app_path'], device_config['app_name'])
            if result != "Emulator started" and result != "Emulator already running":
                raise Exception(f"Failed to start emulator: {result}")
            udid = telegram.udid
            if not udid:
                raise Exception("No UDID detected after starting emulator")
            logging.info(f"Using UDID: {udid} for account {index}")

        sms_activate = SmsApi(service=sms_srvice, api_key_path=sms_api_key_path)
        onion = Onion()

        logging.info("Starting reset device data...")
        reset_telegram_data(telegram.udid)

        # vpn = VPN()
        # vpn.reconnection()

        telegram.start()
        telegram.click_start_messaging()

        number_info = phone_number_send(telegram, sms_activate)
        if not number_info:
            return False
        if number_info == "shut_down":
            return False

        activation_id = number_info[0]
        phone_number = number_info[1]
        number_price = number_info[2]
        username = None
        password = None

        if telegram.check_element(By.XPATH, telegram.ENTER_CODE_TEXT, timeout=2):
            logging.info("No email required, waiting for SMS code")
        else:
            username = generate_random_string(8)
            password = generate_random_string(12)
            onion.reg_and_login(username, password)
            telegram.enter_email(f"{username}@onionmail.org")
            time.sleep(random.uniform(1, 2))

            email_code = onion.extract_code()
            if email_code:
                run_adb_command(f'input text "{email_code}"')
                logging.info(f"Email verification code entered: {email_code}")
            else:
                logging.error("Failed to get email verification code")
                activation_admin(sms_activate)
                return False

        sms_timeout = SMS_TIMEOUT
        while True:
            sms_code = sms_activate.check_verif_status(activation_id, timeout=sms_timeout)
            if sms_code:
                run_adb_command(f'input text "{sms_code}"')
                logging.info(f"SMS code entered: {sms_code}")
                break
            else:
                if telegram.check_element(By.XPATH, telegram.GET_CODE_VIA_SMS, timeout=1):
                    telegram.click_element(By.XPATH, telegram.GET_CODE_VIA_SMS)
                    sms_timeout = 90
                else:
                    logging.error("Failed to get SMS code")
                    activation_admin(sms_activate)
                    return False

        first_name, last_name = check_2fa(telegram,
                                          onion,
                                          sms_activate,
                                          first_names,
                                          last_names,
                                          phone_number,
                                          activation_id)
        
        if not first_name and not last_name and not telegram.check_element(By.XPATH, telegram.MESSAGES_BOX, timeout=2):
            logging.error("Failed to reset account")
            activation_admin(sms_activate)
            return False

        device_info = get_device_info(telegram.udid)
        save_session(phone_number=phone_number,
                     first_name=first_name,
                     last_name=last_name,
                     email_log=f"{username}@onionmail.org" if username else None,
                     email_pass=password,
                     activation_cost=number_price,
                     device_model=device_info['model'],
                     android_v=device_info['android'],
                     tg_v=device_info['tg'],
                     system_lang=device_info['sys_lang'])
        logging.info(f"Account registered successfully: {phone_number}")
        time.sleep(5)

        telegram.click_element(By.XPATH, telegram.ACCEPT_BTN, timeout=3)
        telegram.click_element(By.XPATH, telegram.CONTINUE_BTN, timeout=5)
        telegram.click_element(By.XPATH, telegram.ALLOW_BTN, timeout=5)
        time.sleep(2)
        telegram.click_element(By.XPATH, telegram.ALLOW_BTN, timeout=5)

        create_tdata_with_telegram_desktop(telegram, phone_number)
        return True

    except Exception as e:
        logging.error(f"Registration failed for account {index}: {str(e)}")
        sms_activate.setStatus(activation_id, status=8) if activation_id else None
        return False
    finally:
        if telegram is not None:
            telegram.close()
        activation_admin(sms_activate)


def get_device_config(num_threads, is_physical):
    devices = []
    if is_physical:
        udid = input("Enter UDID of your physical device: ").strip()
        if not udid:
            raise ValueError("UDID cannot be empty for physical device")
        port = input("Enter Appium port for physical device (default 4723): ").strip() or "4723"
        try:
            port = int(port)
            if port < 1024 or port > 65535:
                raise ValueError("Port must be between 1024 and 65535")
        except ValueError:
            raise ValueError("Invalid port number")
        devices.append({
            'is_physical': True,
            'udid': udid,
            'appium_port': port,
            'app_path': None,
            'app_name': None
        })
    else:
        emulator_app_path = input("Enter emulator app path (default: C:\\LDPlayer\\LDPlayer9\\dnplayer.exe): ").strip() or 'C:\\LDPlayer\\LDPlayer9\\dnplayer.exe'
        emulator_app_name = input("Enter emulator app name (default: dnplayer.exe): ").strip() or 'dnplayer.exe'
        for i in range(num_threads):
            port = input(f"Enter Appium port for emulator {i + 1} (default 4723): ").strip() or "4723"
            try:
                port = int(port)
                if port < 1024 or port > 65535:
                    raise ValueError(f"Port for emulator {i + 1} must be between 1024 and 65535")
            except ValueError:
                raise ValueError(f"Invalid port number for emulator {i + 1}")
            devices.append({
                'is_physical': False,
                'udid': None,
                'appium_port': port,
                'app_path': emulator_app_path,
                'app_name': emulator_app_name
            })
    return devices


def main():
    cech_data = setup_cech()

    sms_api_key_path = input("Enter path for file with API key for SMS service: ").strip()
    if not sms_api_key_path:
        sms_api_key_path = 'sms_activate_api.txt'
    sms_service = input("Enter sms service (sms-activate, grizzly-sms, etc.): ")
    cech_data['sms_api_key_path'] = sms_api_key_path
    write_json(cech_data, CECH_PATH)

    device_type = input("Run on emulator (E) or physical device (P): ").strip().upper()
    while device_type not in ['E', 'P']:
        print("Invalid input. Please enter 'E' for emulator or 'P' for physical device.")
        device_type = input("Run on emulator (E) or physical device (P): ").strip().upper()
    is_physical = device_type == 'P'

    first_names_file = input("Enter path to file with first names (default: names.txt): ").strip() or 'names.txt'
    last_names_file = input("Enter path to file with last names (default: second_names.txt): ").strip() or 'second_names.txt'

    first_names = load_names(first_names_file) if os.path.isfile(first_names_file) else []
    last_names = load_names(last_names_file) if os.path.isfile(last_names_file) else []

    num_accounts = int(input("Enter number of accounts to register: "))

    try:
        devices = get_device_config(1, is_physical)  # Single thread
    except ValueError as e:
        logging.error(f"Configuration error: {str(e)}")
        return

    registered_accounts = 0
    attempt = 0
    device_config = devices[0]  # Only one device config

    # Sequential execution for each account
    while registered_accounts < num_accounts:
        attempt += 1
        logging.info(f"Attempting to register account {attempt}")
        success = register_account(device_config, sms_service, sms_api_key_path, first_names, last_names, attempt)
        if success:
            registered_accounts += 1
            logging.info(f"Account registration successful. Total successful: {registered_accounts}/{num_accounts}")
        else:
            logging.error(f"Account registration failed for account {attempt}")

    # Close emulator if used
    if not is_physical:
        kill_emulator(device_config['app_name'])

    logging.info(f"Registration complete. Successfully registered {registered_accounts} of {num_accounts} accounts")


if __name__ == "__main__":
    main()
