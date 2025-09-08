import random
import subprocess
import time
import logging
import os
from auto_reger.utils import load_names, get_device_config, kill_emulator, generate_random_string, save_instagram_data
from auto_reger.emulator import Instagram
from auto_reger.app import Onion, VPN
from auto_reger.adb import reset_data
from selenium.webdriver.common.by import By

logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')


def register_instagram_account(device_config, first_names, last_names, index, is_lite):
    try:
        is_physical = device_config.get('is_physical', False)
        if is_physical:
            udid = device_config['udid']
            instagram = Instagram(udid=udid, appium_port=device_config['appium_port'], is_lite=is_lite)
            logging.info(f"Using physical device with UDID: {udid} for account {index}")
        else:
            instagram = Instagram(appium_port=device_config['appium_port'], is_lite=is_lite)
            logging.info(f"Starting emulator for account {index}")
            result = instagram.start_emulator(device_config['app_path'], device_config['app_name'])
            if result != "Emulator started" and result != "Emulator already running":
                raise Exception(f"Failed to start emulator: {result}")
            udid = instagram.udid
            if not udid:
                raise Exception("No UDID detected after starting emulator")
            logging.info(f"Using UDID: {udid} for account {index}")

        onion = Onion()
        vpn = VPN()

        logging.info("Starting reset instagram data...")
        reset_data(instagram.udid, instagram.INSTAGRAM_ADB_NAME)

        vpn.reconnection()

        instagram.start()
        logging.info("Instagram started")
        instagram.click_element(By.XPATH, instagram.ALLOW_BTN)
        instagram.click_element(By.XPATH, instagram.CREATE_ACC_BTN)
        instagram.click_element(By.XPATH, instagram.CREATE_BY_EMAIL)
        logging.info("Instagram create by email pressed")
        if instagram.check_element(By.XPATH, instagram.EMAIL_FIELD):
            username_email = generate_random_string(12)
            password_email = generate_random_string(12)
            email = onion.reg_and_login(username_email, password_email)
            subprocess.run(f'adb shell input text "{email}"')
            logging.info("Email enter to email field")
            instagram.click_element(By.XPATH, instagram.NEXT_BTN)
        else:
            raise Exception(f"Not found email field")

        time.sleep(random.uniform(1, 3))
        email_code = onion.extract_code('instagram')
        if email_code:
            subprocess.run(f'adb shell input text "{email_code}"')
            logging.info(f"Email verification code entered: {email_code}")
        else:
            logging.error("Failed to get email verification code")
            return False

        time.sleep(random.uniform(1, 2))
        instagram.click_element(By.XPATH, instagram.NEXT_BTN)
        if instagram.check_element(By.XPATH, instagram.PASS_FIELD):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            full_name = f'{first_name}%s{last_name}'
            subprocess.run(f'adb shell input text "{full_name}"')
            password_inst = generate_random_string(12)
            instagram.click_element(By.XPATH, instagram.PASS_FIELD)
            subprocess.run(f'adb shell input text "{password_inst}"')
            time.sleep(random.uniform(1, 2))
            instagram.click_element(By.XPATH, instagram.NEXT_BTN_IN_PASS_ENTER)
        else:
            raise Exception(f"Not found full name field")

        instagram.choose_random_birth_date()
        time.sleep(random.uniform(1, 2))
        instagram.click_element(By.XPATH, instagram.NEXT_BTN)

        if instagram.check_element(By.XPATH, instagram.CHANGE_USERNAME_BTN):
            instagram.click_element(By.XPATH, instagram.CHANGE_USERNAME_BTN)
            time.sleep(2)
            user_name_field = instagram.driver.find_element(By.XPATH, instagram.USERNAME_FIELD)
            username = user_name_field.text
            time.sleep(random.uniform(1, 2))
            instagram.click_element(By.XPATH, instagram.NEXT_BTN)
        else:
            raise Exception(f"Not found change username button")

        if instagram.wait_for_element_to_disappear(By.XPATH, instagram.USERNAME_FIELD, 30):
            instagram.click_element(By.XPATH, instagram.SKIP_CONTACTS_BTN, 3)
            instagram.click_element(By.XPATH, instagram.SKIP_ADD_PHOTO_BTN, 3)

            logging.info(f"Account registered successfully: {index} | {username}:{password_inst}:{email}:{password_email}")
            save_instagram_data({
                'login': username,
                'password': password_inst,
                'email': email,
                'email_password': password_email
            })
            return True

    except Exception as e:
        logging.error(f"Registration failed for account {index}: {str(e)}")
        return False


def main():
    start_time = time.time()

    registered_accounts = 0
    try:
        device_type = input("Run on emulator (E) or physical device (P): ").strip().upper()
        while device_type not in ['E', 'P']:
            print("Invalid input. Please enter 'E' for emulator or 'P' for physical device.")
            device_type = input("Run on emulator (E) or physical device (P): ").strip().upper()
        is_physical = device_type == 'P'

        first_names_file = input("Enter path to file with first names (default: names.txt): ").strip() or 'names.txt'
        last_names_file = input(
            "Enter path to file with last names (default: second_names.txt): ").strip() or 'second_names.txt'

        first_names = load_names(first_names_file) if os.path.isfile(first_names_file) else []
        last_names = load_names(last_names_file) if os.path.isfile(last_names_file) else []

        num_accounts = int(input("Enter number of accounts to register: "))
        is_lite = input("Instagram app is lite version or classic? ('yes' if Lite, 'no' if Classic): ").strip()
        is_lite = True if is_lite == 'yes' else False
        try:
            devices = get_device_config(1, is_physical)  # Single thread
        except ValueError as e:
            logging.error(f"Configuration error: {str(e)}")
            return

        attempt = 0
        device_config = devices[0]  # Only one device config

        # Sequential execution for each account
        while registered_accounts < num_accounts:
            attempt += 1
            logging.info(f"Attempting to register account {attempt}")
            success = register_instagram_account(
                device_config=device_config,
                first_names=first_names,
                last_names=last_names,
                index=attempt,
                is_lite=is_lite
            )
            if success:
                registered_accounts += 1
                logging.info(f"Account registration successful. Total successful: {registered_accounts}/{num_accounts}")
            else:
                logging.error(f"Account registration failed for account {attempt}")

        # Close emulator if used
        if not is_physical:
            kill_emulator(device_config['app_name'])

        logging.info(f"Registration complete. Successfully registered {registered_accounts} of {num_accounts} accounts")
    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time
        per_account = elapsed_time / registered_accounts
        print(f"Скрипт выполнен за {(elapsed_time / 60):.2f} минут")
        print(f"Среднее время на 1 аккаунт {(per_account / 60):.2f} минут")


if __name__ == '__main__':
    main()