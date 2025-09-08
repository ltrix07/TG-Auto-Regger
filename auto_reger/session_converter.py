import os
import sys
import logging
import asyncio
import subprocess
import struct
from auto_reger.decryptor import get_auth_key_and_dc_id
from telethon.sessions import SQLiteSession, MemorySession
from telethon.sync import TelegramClient
from telethon.crypto import AuthKey
from datetime import datetime
from TGConvertor.manager import SessionManager
from AndroidTelePorter import AndroidSession


logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')


class Converter:
    DC_IPS = {
        1: "149.154.175.50",
        2: "149.154.167.51",
        3: "149.154.175.100",
        4: "149.154.167.91",
        5: "91.108.56.130"
    }

    def __init__(self, session_folder: str):
        self.session_folder = session_folder
        os.makedirs(self.session_folder, exist_ok=True)

    async def tdata_to_session(self, tdata_path):
        try:
            account_name = os.path.basename(os.path.dirname(tdata_path.rstrip("/\\")))
            session_path = os.path.join(self.session_folder, f"{account_name}.session")

            acc_data = get_auth_key_and_dc_id(tdata_path)
            auth_key = bytes.fromhex(acc_data['auth_key'])
            dc_id = acc_data['dc_id']
            user_id = acc_data['user_id']

            session = SessionManager(auth_key=auth_key, user_id=user_id, dc_id=dc_id)
            await session.to_telethon_file(session_path)

            print(f'✅ Конвертировал "{account_name}" → {session_path}')
            return True
        except Exception as e:
            print(f"[!] Ошибка конвертации: {e}")
            return False

    def create_session_from_auth_key(self, session_name, auth_key_hex, dc_id):
        auth_key_bytes = bytes.fromhex(auth_key_hex)

        session = SQLiteSession(os.path.join(self.session_folder, session_name))
        session.set_dc(dc_id, self.DC_IPS[dc_id], 443)
        session.auth_key = AuthKey(auth_key_bytes)
        session.save()

        print(f"Session created and save")
        return session

    def define_client_from_auth_key(self, auth_key_hex, dc_id, api_id, api_hash, **kwargs):
        auth_key_bytes = bytes.fromhex(auth_key_hex)

        session = MemorySession()
        session.set_dc(dc_id, self.DC_IPS[dc_id], 443)
        session.auth_key = AuthKey(auth_key_bytes)

        client = TelegramClient(session, api_id=api_id, api_hash=api_hash, **kwargs)
        return client


def transfer_dat_session():
    script_path = os.path.abspath(sys.argv[0])
    script_dir = os.path.dirname(script_path)

    dest_folder = os.path.join(script_dir, 'sessions', 'dat')
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

        subprocess.run(f'adb pull {temp_tgnet_path} {local_tgnet_path}', check=True)
        subprocess.run(f'adb pull {temp_config_path} {local_config_path}', check=True)

        logging.info("Session files from device was transfer")
    except subprocess.TimeoutExpired:
        print("Ошибка: Сессия ADB завершилась по таймауту")
        process.kill()
        raise


def convert_dat_to_session(phone_number):
    script_path = os.path.abspath(sys.argv[0])
    script_dir = os.path.dirname(script_path)

    tgnet_path = os.path.join(script_dir, 'sessions', 'dat', 'tgnet.dat')
    config_path = os.path.join(script_dir, 'sessions', 'dat', 'userconfing.xml')

    today = datetime.now().strftime('%Y-%m-%d')
    converted_folder = os.path.join(script_dir, 'sessions', 'converted', today)
    os.makedirs(converted_folder, exist_ok=True)

    session_file_name = f'acc_{phone_number}.session'
    session_path = os.path.join(converted_folder, session_file_name)

    try:
        session = AndroidSession.from_tgnet(tgnet_path=tgnet_path, userconfig_path=config_path)
        print(session.auth_key)
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


if __name__ == '__main__':
    converter = Converter('./sessions')
    converter.create_session_from_auth_key(
        'test.session',
        '856e4e20cb1c190fbb9976e8f52926c2d0d6a9ef84a73f62d1a0386fe350465d152d382eb35b27b4d6946a20c00826c8d4f22ced509bf021cb18846f9d1dd483cf5cf9a363332905a1252e8f48208079636ed8f210c0666843dcd683aa093b43a0094b16d27ba29f58a47b9159e9462fc52191c26ef7c1717bcaa9ea31d2fe56f2f960546e88f3084e2ba35496ec06964f2b08a1c0e89ce1ecb006ec93311ba9986ae571da90a649c546de7a08a9ebb29c08e5bbe9dffa260b9f4615da1724f97f888350a89c2e58d1fda4807033e8cd9d74d7c0f42ae7c5afb220753dfe81e1664582205b10c96389a00c2079b3f458b7750fd26820db367cb5f338450666cc',
        1
    )

