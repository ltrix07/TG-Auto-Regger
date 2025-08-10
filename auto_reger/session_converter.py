import os
import re
import asyncio
import logging
import subprocess
from datetime import datetime
from auto_reger.adb_handler import run_adb_command
from AndroidTelePorter import AndroidSession
from telethon.sync import TelegramClient


logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')


API_ID = 6
API_HASH = 'eb06d4abfb49dc3eeb1aeb98ae0f581e'


def transfer_dat_session():
    """Переносит tgnet.dat и userconfig.xml из эмулятора через интерактивную сессию."""
    dest_folder = os.path.join(os.path.dirname(__file__), 'sessions', 'dat')
    os.makedirs(dest_folder, exist_ok=True)
    temp_dir = '/sdcard/'

    # Пути к файлам
    remote_tgnet_path = '/data/data/org.telegram.messenger/files/tgnet.dat'
    remote_config_path = '/data/data/org.telegram.messenger/shared_prefs/userconfing.xml'
    temp_tgnet_path = f'{temp_dir}tgnet.dat'
    temp_config_path = f'{temp_dir}userconfing.xml'
    local_tgnet_path = os.path.join(dest_folder, 'tgnet.dat')
    local_config_path = os.path.join(dest_folder, 'userconfing.xml')

    # Запускаем интерактивную сессию adb shell
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
        f'cp {remote_tgnet_path} {temp_tgnet_path}',
        f'cp {remote_config_path} {temp_config_path}',
        'exit',
        'exit'
    ]

    try:
        stdout, stderr = process.communicate('\n'.join(commands), timeout=10)
        if stderr:
            print(f"Ошибка ADB: {stderr}")
            raise subprocess.CalledProcessError(process.returncode, commands, stderr=stderr)

        run_adb_command(f'adb pull {temp_tgnet_path} {local_tgnet_path}')
        run_adb_command(f'adb pull {temp_config_path} {local_config_path}')

        logging.info("Session files from device was transfer")
    except subprocess.TimeoutExpired:
        print("Ошибка: Сессия ADB завершилась по таймауту")
        process.kill()
        raise


def convert_dat_to_session(phone_number):
    tgnet_path = os.path.join(os.path.dirname(__file__), 'sessions', 'dat', 'tgnet.dat')
    config_path = os.path.join(os.path.dirname(__file__), 'sessions', 'dat', 'userconfing.xml')

    today = datetime.now().strftime('%Y-%m-%d')
    converted_folder = os.path.join(os.path.dirname(__file__), 'sessions', 'converted', today)
    os.makedirs(converted_folder, exist_ok=True)

    session_file_name = f'acc_{phone_number}.session'
    session_path = os.path.join(converted_folder, session_file_name)

    try:
        session = AndroidSession.from_tgnet(tgnet_path=tgnet_path, userconfig_path=config_path)
        session.to_telethon(session_path)
        logging.info(f"Session for acc_{phone_number} created in {session_path}")
        return True
    except Exception as e:
        logging.info(f'Error in creating session for acc_{phone_number}: {e}')
        return False


def convert_dat_to_tdata(phone_number):
    # Базовые пути
    sessions_dir = os.path.join(os.path.dirname(__file__), 'sessions')
    dat_dir = os.path.join(sessions_dir, 'dat')
    tgnet_path = os.path.join(dat_dir, 'tgnet.dat')  # Предполагается, что файлы названы по номеру телефона
    config_path = os.path.join(dat_dir, f'userconfing.xml')

    # Путь для конвертированных TData
    today = datetime.now().strftime('%Y-%m-%d')
    converted_base_dir = os.path.join(sessions_dir, 'converted', today)
    os.makedirs(converted_base_dir, exist_ok=True)

    # Папка для конкретного аккаунта
    account_dir = os.path.join(converted_base_dir, f'acc_{phone_number}')
    os.makedirs(account_dir, exist_ok=True)

    try:
        session = AndroidSession.from_tgnet(tgnet_path=tgnet_path, userconfig_path=config_path)
        session.to_tdata(account_dir)  # Сохраняем TData в папку аккаунта
        logging.info(f"TData for account {phone_number} created in {account_dir}")
        return True
    except Exception as e:
        logging.error(f"Error in creating TData for account {phone_number}: {e}")
        return False


async def check_session(session_path, api_id=None, api_hash=None):
    if api_id and api_hash:
        client = TelegramClient(session=session_path, api_id=api_id, api_hash=api_hash)
    else:
        client = TelegramClient(session=session_path, api_id=API_ID, api_hash=API_HASH)

    me = await client.get_me()
    print(me.stringify())

    return False


if __name__ == '__main__':
    try:
        transfer_dat_session()
        convert_dat_to_session(15674661314)
    except Exception as e:
        print(e)
