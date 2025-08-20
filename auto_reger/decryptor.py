from tdesktop_decrypter.decrypter import TdataReader
from tdesktop_decrypter.cli import display_setting_value
from tdesktop_decrypter.decrypter import NoKeyFileException


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
                return {
                    'dc_id': [dc_id for dc_id in account['dc_auth_keys'].keys()][0],
                    'auth_key': [auth_key for auth_key in account['dc_auth_keys'].values()][0],
                    'user_id': account['user_id']
                }
    except NoKeyFileException as exc:
        print(f"No key file was found. Is the tdata path correct?: {exc}")


if __name__ == '__main__':
    print(
        get_auth_key_and_dc_id(
            r'C:\Users\Владимир\PycharmProjects\TG-Auto-Reg\sessions\converted\2025-08-18\acc_16074181780\tdata'
        )
    )

