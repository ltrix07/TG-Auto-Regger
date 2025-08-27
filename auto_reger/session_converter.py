import os
import sys
import logging
import subprocess
from auto_reger.decryptor import get_auth_key_and_dc_id
from datetime import datetime
from TGConvertor.manager import SessionManager
from AndroidTelePorter import AndroidSession


logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')


class Converter:
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
    transfer_dat_session()
    convert_dat_to_tdata(0000)