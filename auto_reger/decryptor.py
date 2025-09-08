import os
from auto_reger.utils import write_json
from tdesktop_decrypter.decrypter import TdataReader
from tdesktop_decrypter.cli import display_setting_value
from tdesktop_decrypter.decrypter import NoKeyFileException
import subprocess


def display_json(parsed_tdata):
    accounts = [
        {
            "index": account.index,
            "user_id": account.mtp_data.user_id,
            "main_dc_id": account.mtp_data.current_dc_id,
            "dc_auth_keys": {
                dc_id: key.hex().lower() for dc_id, key in account.mtp_data.keys.items()
            },
        }
        for account in parsed_tdata.accounts.values()
    ]

    if parsed_tdata.settings is None:
        settings = None
    else:
        settings = {
            str(k): display_setting_value(v) for k, v in parsed_tdata.settings.items()
        }

    obj = {
        "accounts": accounts,
        "settings": settings,
    }
    return obj


def get_auth_key_and_dc_id(tdata_path, passcode=None):
    reader = TdataReader(tdata_path)
    try:
        parsed_data = reader.read(passcode)
        json_data = display_json(parsed_data)
        for account in json_data['accounts']:
            if account['index'] == 0:
                dc_id = account['main_dc_id']
                auth_key = account['dc_auth_keys'][dc_id]
                user_id = account['user_id']
                return {
                    'dc_id': dc_id,
                    'auth_key': auth_key,
                    'user_id': user_id
                }
    except NoKeyFileException as exc:
        print(f"No key file was found. Is the tdata path correct?: {exc}")


def decrypt_folder_with_accounts(folder_path, country):
    accounts_folder_list = os.listdir(folder_path)
    last_folder = os.path.basename(folder_path)
    items_data = []
    errors = []
    for acc_folder in accounts_folder_list:
        if os.path.isdir(os.path.join(folder_path, acc_folder)):
            tdata_path = os.path.join(folder_path, acc_folder, 'tdata')
            item_data = get_auth_key_and_dc_id(tdata_path)
            if item_data:
                items_data.append(item_data)
                continue

            errors.append(acc_folder)
            print(f"В папке аккаунта {acc_folder} не найдено данных для декодирования")

    print(f"Раскодировано {len(items_data)} аккаунтов")
    file_name = f'{last_folder}_{country}.json'
    write_json(items_data, os.path.join(folder_path, file_name))

    if len(errors) > 0:
        write_json(errors, os.path.join(folder_path, 'errors.json'))

    full_file_path = os.path.join(folder_path, file_name)
    return full_file_path


if __name__ == '__main__':
    data_file_path = decrypt_folder_with_accounts(
        r'C:\Users\Владимир\PycharmProjects\TG-Auto-Reg\sessions\converted\2025-09-06',
        'USA'
    )
    subprocess.run(f'scp {data_file_path} goodfox@192.168.1.116:~/TG_ACCOUNTS_MEGA/market_handler/accounts/')

