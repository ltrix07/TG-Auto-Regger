import time
import win32con
import win32gui
import re
import logging
import psutil
import random
import pyautogui
import pywinauto
from pywinauto.findwindows import ElementNotFoundError
from pywinauto import Application, findwindows


logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')


def maximize_window(window_handle):
    win32gui.ShowWindow(window_handle, win32con.SW_MAXIMIZE)


def get_handle(app_title):
    try:
        handles = findwindows.find_windows(title_re=app_title)
        if handles:
            return handles[0]
        return None
    except findwindows.ElementNotFoundError:
        return None


class App:
    def __init__(self):
        self.handle_title = None
        self.app_name = None

    def start_app(self, app_name=None, app_path = None):
        app = Application(backend="uia")

        if not app_name and not app_path:
            raise Exception("You need to specify app_name or app_path")

        if app_name == 'onion':
            self.handle_title = '.*Google Chrome.*'
            app_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

        if app_name == 'vpn':
            self.handle_title = 'ExpressVPN.*'
            app_path = r'C:\Program Files (x86)\ExpressVPN\expressvpn-ui\ExpressVPN.exe'

        if app_path and 'Telegram.exe' in app_path:
            self.handle_title = 'Telegram'

        handle = get_handle(self.handle_title)

        if handle:
            app.connect(handle=handle)
            return app
        else:
            try:
                app.start(app_path)
                time.sleep(7)
                handle = get_handle(self.handle_title)
                if handle:
                    app.connect(handle=handle)
                    return app
                else:
                    print("Failed to start Chrome or find window")
                    raise RuntimeError("Chrome not started or window not found")
            except Exception as e:
                print(f"Error starting {self.handle_title}: {str(e)}")
                raise

    @staticmethod
    def get_element_by_position(window, control_type, l, t, r, b):
        elements = window.descendants(control_type=control_type)
        for elem in elements:
            rect = elem.rectangle()
            if rect.left == l and rect.top == t and rect.right == r and rect.bottom == b:
                return elem

    def close(self):
        try:
            # Подключаемся к приложению
            app = Application(backend="uia").connect(title_re=self.handle_title)

            # Закрываем главное окно приложения
            app.window(title_re=self.handle_title).close()
            print("Главное окно Telegram закрыто.")

        except Exception as e:
            print(f"Не удалось закрыть главное окно: {e}")

        # Проверяем, остались ли фоновые процессы и завершаем их
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == self.app_name:
                print(f"Найдена фоновая задача: {proc.info['name']}. Завершаем её...")
                proc.kill()
                print("Процесс завершён.")


class Onion(App):
    def __init__(self):
        super().__init__()
        self.app = self.start_app('onion')
        self.window = None

    def capcha_hack(self):
        window = None
        try:
            window = self.app.window(title_re="Один момент.*Google Chrome.*")
            window.wait('visible', timeout=20)
            window.set_focus()

            # Цикл для ожидания чекбокса с перепроверкой окна
            start_time = time.time()
            while time.time() - start_time < 30:
                if not window.exists():
                    logging.info("Окно капчи исчезло во время ожидания")
                    return False

                capcha_checkbox = window.child_window(title='Подтвердите, что вы человек', control_type='CheckBox')
                if capcha_checkbox.exists() and capcha_checkbox.is_visible():
                    break

                time.sleep(3)  # Перепроверка каждые 3 секунды

            else:
                logging.error("Таймаут ожидания чекбокса капчи")
                return False

            # Дополнительная проверка перед кликом
            if not window.exists():
                logging.info("Окно капчи исчезло перед кликом")
                return False

            rect = capcha_checkbox.rectangle()
            center_x = (rect.left + rect.right) // 2 + random.randint(-5, 5)
            center_y = (rect.top + rect.bottom) // 2 + random.randint(-5, 5)

            current_x, current_y = pyautogui.position()
            pyautogui.moveTo(center_x, center_y, duration=random.uniform(0.5, 1.2),
                             tween=pyautogui.easeInOutQuad)
            time.sleep(random.uniform(0.1, 0.3))
            pyautogui.click()
            time.sleep(random.uniform(0.2, 0.5))

            return True
        except ElementNotFoundError as e:
            logging.error("ElementNotFoundError: {e}")
            if window:
                window.print_control_identifiers()
            return False
        except NotImplementedError as e:
            logging.error(f"NotImplementedError: {e}")
            return False
        except Exception as e:
            logging.error(f"General error during capcha_hack: {str(e)}")
            return False

    @staticmethod
    def _is_capcha_window_present(timeout=10):
        try:
            end_time = time.time() + timeout
            while time.time() < end_time:
                windows = findwindows.find_windows(title_re="Один момент.*Google Chrome.*")
                if windows:
                    logging.info(f"Found capcha window: {windows}")
                    return True
                time.sleep(0.5)
            logging.info("Capcha window not found in available windows")
            return False
        except Exception as e:
            logging.error(f"Error checking capcha window: {str(e)}")
            return False

    def reg_and_login(self, username, password, domain=None):
        email = None
        try:
            self.window = self.app.window(title_re="Onion Mail.*Google Chrome.*")
            self.window.wait("ready", timeout=20)
            self.window.set_focus()
            logging.info("Найдено окно браузера с открытой вкладкой почты.")

            try:
                is_inbox_txt = self.window.child_window(title=' INBOX', control_type='Text').exists(timeout=1)
            except ElementNotFoundError:
                is_inbox_txt = False

            if is_inbox_txt:
                buttons = self.window.descendants(control_type="Button")
                target_btn = None
                for btn in buttons:
                    rect = btn.rectangle()
                    if rect.top == 108 and rect.right == 1682 and rect.bottom == 172:
                        target_btn = btn
                        break
                target_btn.click_input()
                logging.info("Активировано главное меню.")

                try:
                    log_out = self.window.child_window(control_type='Hyperlink', title='Log out')
                    log_out.wait("visible", timeout=3)
                except Exception as e:
                    print(f"Not found: {e}")
                    log_out = self.window.child_window(control_type='Hyperlink', title=' Log out')
                    log_out.wait("visible", timeout=3)
                log_out.invoke()
                logging.info("Успешно был произведен выход с прошлой почты.")

            create_acc_btn = self.window.child_window(title=' Create account', control_type='Hyperlink')
            create_acc_btn.wait("visible", timeout=10)
            create_acc_btn.invoke()
            logging.info("Найдена форма для создания нового аккаунта.")

            if self._is_capcha_window_present(timeout=10):
                logging.info("Обнаружено окно капчи, запускаем capcha_hack")
                if self.capcha_hack():
                    logging.info("Capcha passed!")
                else:
                    logging.error("Capcha hack failed")
            else:
                logging.info("Capcha not found, proceeding with login")

            if domain:
                domain_menu = self.window.child_window(control_type='Button', title='@onionmail.org')
                domain_menu.wait("visible", timeout=30)
                domain_menu.click_input()

                domain_item = self.window.child_window(control_type='Hyperlink', title=domain)
                domain_item.wait("visible", timeout=5)
                domain_item.click_input()
                email = username + f'@{domain}'
            else:
                email = username + '@onionmail.org'

            name_field = self.window.child_window(control_type="Edit", auto_id="name")
            name_field.wait("ready", timeout=60)
            name_field.set_text("")
            name_field.type_keys(username, with_spaces=True)
            logging.info("Введено имя пользователя")

            username_field = self.window.child_window(control_type="Edit", auto_id="username")
            username_field.wait("visible", timeout=10)
            username_field.set_text("")
            username_field.type_keys(username, with_spaces=True)
            logging.info("Введено имя почты")

            password_field = self.window.child_window(control_type="Edit", auto_id="password")
            password_field.wait("visible", timeout=10)
            password_field.set_text("")
            password_field.type_keys(password, with_spaces=True)
            logging.info("Введен пароль")

            confirm_password_field = self.window.child_window(control_type="Edit", auto_id="password2")
            confirm_password_field.wait("visible", timeout=10)
            confirm_password_field.set_text("")
            confirm_password_field.type_keys(password, with_spaces=True)
            logging.info("Пароль подтвержден")

            logging.info("Ищем чекбокс...")
            try:
                checkbox = self.window.child_window(control_type='CheckBox', title=" Agree to terms of service")
                checkbox.wait("visible", timeout=1)
            except Exception:
                checkbox = self.window.child_window(control_type='CheckBox', title="Agree to terms of service")
                checkbox.wait("visible", timeout=1)
            checkbox.click_input()
            logging.info("Чекбокс активирован")

            create_account_btn = self.window.child_window(control_type='Button', title='CREATE NEW ACCOUNT')
            create_account_btn.wait("visible", timeout=10)
            create_account_btn.invoke()
            logging.info("Новый аккаунт почты создан")
            time.sleep(5)

            try:
                is_login_txt = self.window.child_window(title=' Log in', control_type='Text').exists(timeout=10)
            except ElementNotFoundError:
                is_login_txt = False

            if is_login_txt:
                username_field_log = self.window.child_window(control_type="Edit", auto_id="username")
                username_field_log.wait("visible", timeout=60)
                username_field_log.set_text("")
                username_field_log.type_keys(username, with_spaces=True)
                logging.info("Имя введено")

                password_field_log = self.window.child_window(control_type="Edit", auto_id="password")
                password_field_log.wait("visible", timeout=60)
                password_field_log.set_text("")
                password_field_log.type_keys(password, with_spaces=True)
                logging.info("Пароль введен")

                try:
                    login_btn = self.window.child_window(control_type="Button", title=' LOG IN')
                    login_btn.wait("visible", timeout=1)
                except Exception as e:
                    print(f"Not found: {e}")
                    login_btn = self.window.child_window(control_type="Button", title='LOG IN')
                    login_btn.wait("visible", timeout=1)
                time.sleep(1)
                login_btn.invoke()
                logging.info("Вход в аккаунт почты выполнен успешно")

        except ElementNotFoundError as e:
            print(f"ElementNotFoundError: {e}")
            self.window.print_control_identifiers()
        except NotImplementedError as e:
            print(f"NotImplementedError: {e}")
        except Exception as e:
            print(f"General error during reg_and_login: {str(e)}")
            self.window.print_control_identifiers()

        return email

    def extract_code(self, time_out=5, second_req=False):
        attempts = 3
        attempt = 0
        try:
            self.window = self.app.window(title_re="Onion Mail.*Google Chrome.*")
            self.window.wait("visible", timeout=20)
            self.window.set_focus()

            code_element = None
            while attempt < attempts:
                reload_page = self.window.child_window(title="Перезагрузить", control_type="Button")
                reload_page.wait("visible", timeout=time_out)
                reload_page.invoke()

                if second_req:
                    code_element = self.window.child_window(title_re=r'.*Dear , Your code is: \d+', control_type='DataItem')
                else:
                    code_element = self.window.child_window(title_re=r'.*Hello Your code is: \d+', control_type='DataItem')

                if code_element.exists(time_out) and code_element.is_visible():
                    break
                else:
                    time.sleep(time_out)
                    attempt += 1

            text = code_element.window_text()
            code = re.search(r"Your Code - (\d+)", text).group(1)
            print(f"Extracted code: {code}")

            return code
        except ElementNotFoundError as e:
            print(f"ElementNotFoundError in extract_code: {e}")
            self.window.print_control_identifiers()
            return None
        except Exception as e:
            print(f"General error in extract_code: {e}")
            self.window.print_control_identifiers()
            return None


class VPN(App):
    def __init__(self):
        super().__init__()
        self.app = self.start_app('vpn')
        self.window = None

    def reconnection(self):
        try:
            window = self.app.window(title_re='ExpressVPN.*')
            window.wait("visible", timeout=20)
            window.set_focus()
            logging.info("Найдено окно VPN приложения")

            disconnect_btn = window.child_window(title_re=r'Отключиться от.*', control_type='Button')
            disconnect_btn.invoke()
            logging.info("Отключение от VPN...")

            connect_btn = window.child_window(title_re=r'Подключитесь к.*', control_type='Button')
            connect_btn.wait("visible", timeout=60)
            connect_btn.invoke()
            logging.info("Подключение к VPN...")

            disconnect_btn.wait("visible", timeout=60)
            logging.info("Смена IP прошла успешно.")
            return True
        except ElementNotFoundError as e:
            print(f"ElementNotFoundError: {e}")
            window.print_control_identifiers()
            return False
        except NotImplementedError as e:
            print(f"NotImplementedError: {e}")
            return False
        except Exception as e:
            print(f"General error during reg_and_login: {str(e)}")
            window.print_control_identifiers()
            return False


class TelegramDesktop(App):
    def __init__(self, app_path):
        super().__init__()
        self.app = self.start_app(app_path=app_path)
        self.app_name = app_path.split('\\')[-1]
        self.window = None

    def start_and_enter_number(self, phone_number):
        try:
            self.window = self.app.window(title='Telegram')
            self.window.wait('ready', timeout=30)

            maximize_window(self.window.handle)
            self.window.set_focus()
            time.sleep(2)
            logging.info("Найдено окно телеграм и открыто на весь экран")

            start_messaging_btn = self.get_element_by_position(self.window, "Group", 772, 641, 1147, 693)
            start_messaging_btn.click_input()
            logging.info('Нажата кнопка "Start messaging'"")

            log_by_number_btn = self.get_element_by_position(self.window, "Group", 827, 726, 1093, 748)
            log_by_number_btn.click_input()
            logging.info('Нажата кнопка "Log in by number"')

            number_input_field = self.get_element_by_position(self.window, "Edit", 772, 479, 852, 555)
            number_input_field.set_text("")
            number_input_field.type_keys(phone_number, with_spaces=True)
            logging.info('Введен номер телефона')

            next_btn = self.get_element_by_position(self.window, "Group", 772, 608, 1147, 660)
            next_btn.click_input()
            logging.info('Запрос на СМС отправлен')

            return True

        except ElementNotFoundError as e:
            print(f"ElementNotFoundError: {e}")
            self.window.print_control_identifiers()
            return False
        except NotImplementedError as e:
            print(f"NotImplementedError: {e}")
            return False
        except Exception as e:
            print(f"General error during start_and_enter_number: {str(e)}")
            self.window.print_control_identifiers()
            return False

    def enter_code(self, code):
        try:
            self.window.set_focus()

            enter_code_field = self.get_element_by_position(self.window, "Group", 778, 417, 827, 479)
            enter_code_field.click_input()
            enter_code_field.type_keys(code, with_spaces=True)

        except ElementNotFoundError as e:
            print(f"ElementNotFoundError: {e}")
            self.window.print_control_identifiers()
            return False
        except NotImplementedError as e:
            print(f"NotImplementedError: {e}")
            return False
        except Exception as e:
            print(f"General error during enter_code: {str(e)}")
            self.window.print_control_identifiers()
            return False


if __name__ == '__main__':
    onion = Onion()
    email = onion.reg_and_login('jgfy8weftyufger', 'jgfy8weftyufger', 'onionmail.com')
    print(email)
