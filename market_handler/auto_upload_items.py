import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from market import market, DESCRIPTION, ACCOUNT_DATA_FOR_COUNTRY, TELEGRAM_CLIENT
from auto_reger.utils import read_json, write_json, load_config
from auto_reger.session_handler import set_2fa_safe


CONFIG = load_config()


# Constants
ACCOUNTS_DIR = Path(CONFIG['auto_upload_app']['path']['accounts'])
UPLOADED_LOG_PATH = Path(CONFIG['auto_upload_app']['path']['uploaded'])
ACTUAL_INFO_PATH = Path(CONFIG['auto_upload_app']['path']['actual_info'])
RESTING_REGION_TIME = CONFIG['auto_upload_app']['resting_region_time']
CHECK_INTERVAL_MINUTES = CONFIG['auto_upload_app']['interval_minutes']


# Helpful functions
def _parse_dir_info(dirname: str):
    """Split dir name on registration date and country"""
    date_str, country_str = dirname.split('_')
    reg_date = datetime.strptime(date_str, '%Y-%m-%d')
    return reg_date, country_str


def _load_uploaded_log():
    """Read data with names of files which was uploaded recently"""
    return read_json(UPLOADED_LOG_PATH) if UPLOADED_LOG_PATH.exists() else {}


def _get_ready_dirs(uploaded_log):
    """Check ready accounts for uploads"""
    today = datetime.now()
    ready = []
    for dirname in os.listdir(ACCOUNTS_DIR):
        dirpath = ACCOUNTS_DIR / dirname
        if not dirpath.is_dir():
            continue
        if dirname in uploaded_log:
            continue

        reg_date, country = _parse_dir_info(dirname)
        delay_days = RESTING_REGION_TIME.get(country, 1)
        if (today - reg_date).days >= delay_days:
            ready.append(dirname)
    return ready


def _collect_accounts_from_dir(dir_name):
    """Collect accounts from dirs which ready"""
    accounts = []
    dir_path = ACCOUNTS_DIR / dir_name
    for f in os.listdir(dir_path):
        if f.endswith(".json"):
            acc = read_json(dir_path / f)  # тут один аккаунт = dict
            acc["user_id"] = Path(f).stem  # добавим user_id = имя файла (номер телефона)
            accounts.append(acc)
    return accounts


def _plan_uploads(dirs):
    """Form a plan of fillings according to priority hours"""
    uploads = []
    dirs_remaining = dirs.copy()
    priority_hours = read_json(ACTUAL_INFO_PATH)

    for slot in priority_hours:
        if not dirs_remaining:
            break

        accounts_batch = []
        for dirname in dirs_remaining[:]:
            accounts_batch.extend(_collect_accounts_from_dir(dirname))
            dirs_remaining.remove(dirname)

            if len(accounts_batch) >= 60:  # максимум 60 за час
                break

        delay = max(60 / len(accounts_batch), 1)
        uploads.append({
            'hour': slot['hour'],
            'accounts': accounts_batch,
            'delay': delay
        })

    return uploads


def _wait_until(hour):
    """Wait priority time for uploading"""
    now = datetime.now()
    target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if now > target:
        target += timedelta(days=1)
    print(f'⏳ Ожидание до {target.strftime("%Y-%m-%d %H:%M")}')
    time.sleep((target - now).total_seconds())


def _upload_file(dir_name, delay_minutes_per_account):
    """Upload account logic"""
    reg_date, country = _parse_dir_info(dir_name)
    country_data = ACCOUNT_DATA_FOR_COUNTRY[country]
    items_data = _collect_accounts_from_dir(dir_name)

    for idx, item in enumerate(items_data, start=1):
        auth_key = item['auth_data']['auth_key']
        dc_id = item['auth_data']['dc_id']
        cloud_password = item['telegram_2fa']['password']
        hint = item['telegram_2fa']['hint']

        # Reset 2fa from telegram account
        set_2fa_safe(auth_key=auth_key, dc_id=dc_id, country=country, password=None, cur_password=cloud_password,
                     hint=hint)

        information = None
        has_email_login_data = False

        # Add information for buyer if account was registration with email
        if item['email_login']:
            has_email_login_data = True
            information = (f'Если Вы видите это сообщение значит аккаунт был зарегистрирован с почтой.\n'
                           f'Сервис: https://onionmail.org/\n'
                           f'{item["email_login"]}:{item["email_password"]}')

        # Upload account on market
        response = market.publishing.fast(
            title=country_data['title'],
            title_en=country_data['title_en'],
            description=DESCRIPTION,
            price=country_data['price'],
            origin='autoreg',
            category_id=24,
            currency='usd',
            login=auth_key,
            password=dc_id,
            proxy_random=True,
            has_email_login_data=has_email_login_data,
            email_login_data=f"{item['email_login']}:{item['email_password']}",
            email_type='autoreg',
            information=information,
            extra={'checkChannels': True, 'checkSpam': True, "telegramClient": TELEGRAM_CLIENT}
        )
        if response.status_code == 200:
            print(f"✅ {item['user_id']} ({idx}/{len(items_data)}) — uploaded successfully!")
        else:
            print(f"❌ {item['user_id']} — error: {response.json().get('errors')}")

        if idx < len(items_data):
            time.sleep(delay_minutes_per_account * 60)


# Main circle
def main():
    # Read uploaded recently accounts
    uploaded_log = _load_uploaded_log()
    while True:
        # Get accounts which ready for upload
        ready_files = _get_ready_dirs(uploaded_log)
        if ready_files:
            print(f'📦 Find {len(ready_files)} new files for upload')
            upload_plan = _plan_uploads(ready_files)
            for slot in upload_plan:
                # Waiting to start priority hour
                _wait_until(slot['hour'])
                start_time = datetime.now()

                for file in slot['files']:
                    _upload_file(file, slot['delay'])
                    uploaded_log[file] = datetime.now().isoformat()
                    write_json(uploaded_log, UPLOADED_LOG_PATH)

                    # Recheck: have you gone beyond the hour limit
                    if (datetime.now() - start_time).seconds >= 3600:
                        print("⏱ Hour is end, waiting for next")
                        break
        else:
            if CHECK_INTERVAL_MINUTES < 60:
                print(f'🔍 Have not new accounts. Recheck again after {CHECK_INTERVAL_MINUTES} minutes.')
            else:
                print(f'🔍 Have not new accounts. Recheck again after {CHECK_INTERVAL_MINUTES / 60} hours.')
        time.sleep(CHECK_INTERVAL_MINUTES * 60)


if __name__ == '__main__':
    main()
