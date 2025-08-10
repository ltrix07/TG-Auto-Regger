import subprocess
import socket
import time
import re
import random
import logging
from auto_reger.adb_handler import connect_adb, get_device_info, run_adb_command
from appium.webdriver.appium_service import AppiumService
from appium.options.common import AppiumOptions
from appium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# Настройка логирования
logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')


class Emulator:
    adb_user = input('ADB path (default: C:\\Android\\platform-tools\\adb.exe): ')
    ADB_PATH = r"C:\Android\platform-tools\adb.exe" if adb_user == '' else adb_user

    START_MESSAGING_BTN = '//android.widget.TextView[@text="Start Messaging"]'
    CONTINUE_ENGLISH = '//android.widget.TextView[@text="Continue in English"]'
    COUNTRY_CODE_INPUT = '//android.widget.EditText[@content-desc="Country code"]'
    PHONE_NUMBER_INPUT = '//android.widget.EditText[@content-desc="Phone number"]'
    DONE_BTN = '//android.widget.FrameLayout[@content-desc="Done"]/android.view.View'
    YES_BTN = '//android.widget.TextView[@text="Yes"]'
    EMAIL_INPUT = '//android.widget.EditText'
    CONTINUE_BTN = '//android.widget.TextView[@text="Continue"]'
    ALLOW_BTN = '//android.widget.Button[@resource-id="com.android.packageinstaller:id/permission_allow_button"]'
    ALLOW_CALLING_MESSAGE = '//android.widget.TextView[@resource-id="com.android.packageinstaller:id/permission_message"]'
    ALLOW_CALLING_LIST_MESSAGE = ('//android.widget.TextView[@resource-id="com.android.packageinstaller:id/permission_message"]')
    TELEGRAM_APP = '//android.widget.TextView[@content-desc="Telegram"]'
    NAME_FIELD = '//android.widget.ScrollView/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout[2]/android.widget.FrameLayout[1]/android.widget.EditText'
    LAST_NAME_FIELD = '//android.widget.ScrollView/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout[2]/android.widget.FrameLayout[2]/android.widget.EditText'
    MENU_BTN = '//android.widget.ImageView[@content-desc="Open navigation menu"]'
    SETTINGS_BTN = '(//android.widget.TextView[@text="Settings"])[1]/android.view.View'
    MORE_OPTIONS = '//android.widget.ImageButton[@content-desc="More options"]/android.widget.ImageView'
    LOG_OUT_OPTIONS = '//android.widget.TextView[@text="Log Out"]'
    LOG_OUT_BTN = '(//android.widget.TextView[@text="Log Out"])[2]'
    CHAT_WITH_TELEGRAM = '//android.view.ViewGroup'
    NUMBER_IS_BANNED = '//android.widget.TextView[@text="This phone number is banned."]'
    OK_BTN = '//android.widget.TextView[@text="OK"]'
    PASS_NEED_TEXT = '//android.widget.TextView[@text="Two-Step Verification enabled. Your account is protected with an additional password."]'
    FORGOT_PASS_BTN = '//android.widget.TextView[@text="Forgot password?"]'
    RESET_ACC_BTN = '//android.widget.TextView[@text="Reset account"]'
    CHECK_EMAIL_TEXT = '//android.widget.TextView[@text="Check Your Email"]'
    TOO_MANY_ATTEMPTS = '//android.widget.TextView[@text="Too many attempts, please try again later."]'
    ENTER_CODE_TEXT = '//android.widget.TextView[@text="Enter code"]'

    def __init__(self, udid=None, appium_port=4723, emulator_path=None, emulator_name=None, physical_device=False):
        self.udid = udid
        self.appium_port = appium_port
        self.emulator_path = emulator_path
        self.emulator_name = emulator_name
        self.driver = None
        self.appium_service = None

        if physical_device:
            self.udid = input("Input UDID of your physical device: ")
        else:
            # Проверка подключения ADB, если UDID уже известен
            if self.udid and not connect_adb(self.udid):
                logging.error(f"Failed to connect to ADB for {self.udid}")
                raise RuntimeError(f"Failed to connect to ADB for {self.udid}")

            # Вывод списка устройств
            process = subprocess.Popen(f'"{self.ADB_PATH}" devices', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output, error = process.communicate()
            if error:
                logging.error(f"Error listing devices: {error.decode()}")
                raise RuntimeError(f"Error listing devices: {error.decode()}")
            logging.info(f"Connected devices: {output.decode()}")

        # Информация об устройстве, если UDID известен
        if self.udid:
            get_device_info(self.udid)

        # Проверка, свободен ли порт Appium
        if not self._is_port_free(appium_port):
            logging.error(f"Appium port {appium_port} is already in use")
            raise RuntimeError(f"Appium port {appium_port} is already in use")

        # Запуск Appium-сервера
        self.appium_service = AppiumService()
        try:
            self.appium_service.start(args=['--address', '127.0.0.1', '--port', str(appium_port)])
            logging.info(f"Appium service started on port {appium_port}")
        except Exception as e:
            logging.error(f"Failed to start Appium service: {e}")
            raise RuntimeError(f"Failed to start Appium service: {e}")

    @staticmethod
    def _is_port_free(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) != 0

    @staticmethod
    def get_emulator_udid():
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        devices = [line.split('\t')[0] for line in result.stdout.splitlines() if '\tdevice' in line]
        return devices[0] if devices else None

    def is_emulator_running(self):
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        return self.udid in result.stdout and 'device' in result.stdout if self.udid else False

    def start_emulator(self, app_path, app_name):
        if not self.is_emulator_running():
            logging.info(f"Starting emulator: {app_path}")
            process = subprocess.Popen(app_path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(30)  # Ожидание загрузки эмулятора
            self.udid = self.get_emulator_udid()
            if not self.udid:
                logging.error("Failed to get UDID after starting emulator")
                raise Exception("Failed to get UDID after starting emulator")
            logging.info(f"Emulator started with UDID: {self.udid}")
            return "Emulator started"
        logging.info(f"Emulator already running with UDID: {self.udid}")
        return "Emulator already running"

    def check_app_installed(self, app_package):
        process = subprocess.Popen(f'"{self.ADB_PATH}" -s {self.udid} shell pm list packages {app_package}',
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        return app_package in output.decode()

    def do_activity(self, app_package=None, app_activity=None):
        if not self.udid:
            logging.error("UDID not set. Start emulator first.")
            raise RuntimeError("UDID not set. Start emulator first.")
        if app_package and not self.check_app_installed(app_package):
            logging.error(f"Application {app_package} is not installed on {self.udid}")
            raise RuntimeError(f"Application {app_package} is not installed on {self.udid}")

        capabilities = {
            "platformName": "Android",
            "appium:deviceName": self.udid,
            "appium:udid": self.udid,
            "appium:noReset": False,
            "appium:automationName": "UiAutomator2",
            "appium:newCommandTimeout": 300,
            "appium:adbExecTimeout": 60000,
            "appium:forceAppiumServerApkInstall": True,
            "appium:enforceAppInstall": True,
            "appium:skipDeviceInitialization": True,
            "appium:enforceXPath1": True
        }

        if app_package and app_activity:
            capabilities['appium:appPackage'] = app_package
            capabilities['appium:appActivity'] = app_activity

        options = AppiumOptions()
        options.load_capabilities(capabilities)

        try:
            self.driver = webdriver.Remote(f"http://127.0.0.1:{self.appium_port}", options=options)
            logging.info(f"WebDriver created for {self.udid}")
        except Exception as e:
            logging.error(f"Failed to create WebDriver: {e}")
            raise RuntimeError(f"Failed to create WebDriver: {e}")

    def check_element(self, by, value, timeout=5):
        wait = WebDriverWait(self.driver, timeout)
        try:
            return wait.until(EC.presence_of_element_located((by, value)))
        except (TimeoutException, NoSuchElementException):
            logging.error(f"Элемент {value} не появился за {timeout} секунд")
            return False

    def wait_for_element_to_disappear(self, by, value, timeout=10):
        wait = WebDriverWait(self.driver, timeout)
        try:
            return wait.until(EC.invisibility_of_element_located((by, value)))
        except (TimeoutException, NoSuchElementException):
            logging.error(f"Элемент {value} не исчез за {timeout} секунд")
            return False

    def check_element_present(self, by1, value1, by2, value2, timeout=5):
        wait = WebDriverWait(self.driver, timeout)

        try:
            wait.until(EC.presence_of_element_located((by1, value1)))
            return "element1"
        except (TimeoutException, NoSuchElementException):
            pass

        try:
            wait.until(EC.presence_of_element_located((by2, value2)))
            return "element2"
        except (TimeoutException, NoSuchElementException):
            logging.info(f"Neither element {value1} nor {value2} appeared on the screen.")
            return None

    def click_element(self, by, value, timeout=30):
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.element_to_be_clickable((by, value)))
            element.click()
            time.sleep(random.uniform(1, 2))
        except (TimeoutException, NoSuchElementException):
            logging.error(f"Элемент {value} не найден за {timeout} секунд")
            return False

    def send_keys(self, by, value, keys, timeout=30):
        wait = WebDriverWait(self.driver, timeout)
        element = wait.until(EC.presence_of_element_located((by, value)))
        element.click()
        element.clear()
        element.send_keys(keys)
        time.sleep(random.uniform(1, 2))

    def close(self):
        if self.appium_service is not None:
            try:
                self.appium_service.stop()
                logging.info("Appium service stopped")
            except Exception as e:
                logging.error(f"Error stopping Appium service: {e}")
            self.appium_service = None

    def randomize_device(self):
        import secrets
        # Смена Android ID
        new_android_id = secrets.token_hex(8)
        subprocess.run(f'adb -s {self.udid} shell settings put secure android_id {new_android_id}', shell=True)

        # Смена MAC-адреса
        new_mac = ':'.join(['{:02x}'.format(random.randint(0, 255)) for _ in range(6)])
        subprocess.run(f'adb -s {self.udid} shell "ip link set wlan0 address {new_mac}"', shell=True)

        # Смена разрешения экрана
        resolutions = ['1080x1920', '720x1280', '1440x2560']
        densities = random.choice([320, 480, 560])
        subprocess.run(f'adb -s {self.udid} shell wm size {random.choice(resolutions)}', shell=True)
        subprocess.run(f'adb -s {self.udid} shell wm density {random.choice(densities)}', shell=True)

        # Смена часового пояса
        timezones = ['America/New_York', 'Europe/Moscow', 'Asia/Tokyo']
        subprocess.run(f'adb -s {self.udid} shell setprop persist.sys.timezone {random.choice(timezones)}',
                       shell=True)

    def __del__(self):
        self.close()


class Telegram(Emulator):
    def __init__(self, udid=None, appium_port=4723, emulator_path=None, emulator_name=None):
        super().__init__(udid, appium_port, emulator_path, emulator_name)
        self.app_package = 'org.telegram.messenger'
        self.app_action_for_start = 'org.telegram.messenger/org.telegram.ui.LaunchActivity'

    def start(self, like_human=True):
        if not self.check_app_installed(self.app_package):
            logging.error(f"Telegram ({self.app_package}) is not installed on {self.udid}")
            raise RuntimeError(f"Telegram ({self.app_package}) is not installed on {self.udid}")

        if not like_human:
            self.do_activity(self.app_package, self.app_action_for_start)
        else:
            self.do_activity()
            self.click_element(By.XPATH, self.TELEGRAM_APP, 10)

    def reconnection(self):
        self.do_activity()

    def reset_app(self):
        if self.driver:
            try:
                self.driver.terminate_app(self.app_package)
                process = subprocess.Popen(
                    f'"{self.ADB_PATH}" -s {self.udid} shell pm clear {self.app_package}',
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
                )
                output, error = process.communicate()
                if error:
                    logging.error(f"Failed to clear app data: {error.decode()}")
                    raise RuntimeError(f"Failed to clear app data: {error.decode()}")
                logging.info(f"App {self.app_package} cleared")
            except Exception as e:
                logging.error(f"Error resetting app: {e}")
        self.start()

    def click_start_messaging(self):
        try:
            self.click_element(By.XPATH, self.START_MESSAGING_BTN, 60)

            if self.check_element(By.XPATH, self.CONTINUE_BTN, timeout=10):
                self.click_element(By.XPATH, self.CONTINUE_BTN)

            if self.click_element(By.XPATH, '//android.widget.Button[@resource-id="com.android.packageinstaller:id/permission_allow_button"]', timeout=5):
                self.click_element(By.XPATH, '//android.widget.Button[@resource-id="com.android.packageinstaller:id/permission_allow_button"]')

        except (TimeoutException, NoSuchElementException):
            if self.check_element(By.XPATH, self.CONTINUE_ENGLISH, 2):
                self.click_element(By.XPATH, self.CONTINUE_ENGLISH)

            if self.check_element(By.XPATH, self.CONTINUE_BTN, timeout=3):
                self.click_element(By.XPATH, self.CONTINUE_BTN)

            if self.click_element(By.XPATH, '//android.widget.Button[@resource-id="com.android.packageinstaller:id/permission_allow_button"]', timeout=5):
                self.click_element(By.XPATH, '//android.widget.Button[@resource-id="com.android.packageinstaller:id/permission_allow_button"]')

    def send_number(self, number, timeout=5):
        wait = WebDriverWait(self.driver, timeout)
        try:
            phone_number_field = wait.until(EC.presence_of_element_located((By.XPATH, self.PHONE_NUMBER_INPUT)))
        except (TimeoutException, NoSuchElementException):
            logging.error("Элемент для ввода номера не найден")
            return
        phone_number_field.clear()

        self.send_keys(By.XPATH, self.COUNTRY_CODE_INPUT, number)
        self.click_element(By.XPATH, self.DONE_BTN)
        self.click_element(By.XPATH, self.YES_BTN, timeout=3)

        if self.check_element(By.XPATH, self.CONTINUE_BTN, timeout=2):
            self.click_element(By.XPATH, self.CONTINUE_BTN)

        if self.check_element(By.XPATH, '//android.widget.Button[@resource-id="com.android.packageinstaller:id/permission_allow_button"]', timeout=2):
            self.click_element(By.XPATH, '//android.widget.Button[@resource-id="com.android.packageinstaller:id/permission_allow_button"]')

    def click_continue_second_windows(self, timeout=2):
        try:
            self.click_element(By.XPATH, self.CONTINUE_BTN, timeout)
        except (TimeoutException, NoSuchElementException):
            pass

    def click_allow_btn(self, timeout=2):
        if self.check_element(By.XPATH, self.ALLOW_CALLING_MESSAGE, timeout):
            self.click_element(By.XPATH, self.ALLOW_BTN)

        if self.check_element(By.XPATH, self.ALLOW_CALLING_LIST_MESSAGE, timeout):
            self.click_element(By.XPATH, self.ALLOW_BTN)

    def enter_email(self, email):
        self.send_keys(By.XPATH, self.EMAIL_INPUT, email)
        self.click_element(By.XPATH, self.DONE_BTN)

    def click_on_chat_with_telegram(self, timeout=10):
        self.click_element(By.XPATH, self.CHAT_WITH_TELEGRAM, timeout)

    def enter_name(self, name, last_name):

        self.send_keys(By.XPATH, self.NAME_FIELD, name, timeout=2)
        self.send_keys(By.XPATH, self.LAST_NAME_FIELD, last_name, timeout=2)
        self.click_element(By.XPATH, self.DONE_BTN, timeout=2)

    def read_sms_with_code(self, timeout=60):
        telegram_chat = '//android.view.ViewGroup'
        message_xpath = '//android.view.ViewGroup[contains(@text, "Код для входа в Telegram: ")]'
        if self.check_element(By.XPATH, telegram_chat, timeout):
            self.click_element(By.XPATH, telegram_chat, timeout)
            try:
                wait = WebDriverWait(self.driver, timeout)
                message_element = wait.until(EC.presence_of_element_located((By.XPATH, message_xpath)))
                logging.info("Message element found")

                # Получение текста элемента
                message_text = message_element.get_attribute('text')
                logging.info(f"Message text: {message_text}")

                # Извлечение кода с помощью регулярного выражения
                code_pattern = r'Код для входа в Telegram: (\d{5})'
                match = re.search(code_pattern, message_text)
                if match:
                    code = match.group(1)
                    logging.info(f"Code found: {code}")
                    return code

                logging.error("Code not found in message text")
                return None

            except Exception as e:
                logging.error(f"Error extracting code: {str(e)}")
                return None

    def account_log_out(self):
        self.click_element(By.XPATH, self.MENU_BTN)
        self.click_element(By.XPATH, self.SETTINGS_BTN)
        self.click_element(By.XPATH, self.MORE_OPTIONS)
        self.click_element(By.XPATH, self.LOG_OUT_OPTIONS)
        self.click_element(By.XPATH, self.LOG_OUT_BTN)
        self.click_element(By.XPATH, self.LOG_OUT_BTN)
