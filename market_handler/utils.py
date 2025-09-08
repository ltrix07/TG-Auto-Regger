import json
import subprocess
import time
import psutil
import random
import logging
import os
from datetime import datetime


logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')


def read_json(path):
    with open(path, 'r', encoding='utf-8') as f_o:
        return json.load(f_o)


def write_json(obj, path):
    with open(path, 'w', encoding='utf-8') as f_o:
        return json.dump(obj, f_o, indent=4)


def read_txt_list(file_path):
    with open(file_path, 'r', encoding='utf-8') as f_o:
        return f_o.readlines()


def load_names(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def generate_random_string(length=8):
    import string
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))


def save_instagram_data(new_data):
    data_dir = 'instagram'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    today = datetime.now().strftime('%Y-%m-%d')
    today_file_name = os.path.join(data_dir, f'{today}_accounts.json')

    if os.path.exists(today_file_name):
        with open(today_file_name, 'r') as f:
            accounts = json.load(f)
    else:
        accounts = []

    accounts.append(new_data)

    with open(today_file_name, 'w') as f:
        json.dump(accounts, f, indent=4)


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


def _is_process_running(process_name):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'].lower() == process_name.lower():
            return True
    return False


def kill_emulator(app_name):
    if _is_process_running(app_name):
        subprocess.run(f"taskkill /IM {app_name} /F", shell=True, capture_output=True)
        time.sleep(2)
        logging.info(f"Emulator {app_name} terminated")
    else:
        logging.info(f"Emulator {app_name} is not running, no need to terminate")
