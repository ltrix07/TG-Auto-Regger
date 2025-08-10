import time
import re
import logging
from pywinauto.findwindows import ElementNotFoundError
from pywinauto import Application, findwindows


logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')


def get_handle(app_title):
    try:
        handles = findwindows.find_windows(title_re=app_title)
        if handles:
            return handles[0]
        return None
    except findwindows.ElementNotFoundError:
        return None


class App:
    def start_app(self, app_name):
        app = Application(backend="uia")
        handle_title = None
        app_path = None

        if app_name == 'onion':
            handle_title = 'Onion Mail.*Google Chrome.*'
            app_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

        if app_name == 'vpn':
            handle_title = 'ExpressVPN.*'
            app_path = r'C:\Program Files (x86)\ExpressVPN\expressvpn-ui\ExpressVPN.exe'

        handle = get_handle(handle_title)

        if handle:
            app.connect(handle=handle)
            return app
        else:
            try:
                app.start(app_path)
                time.sleep(7)
                handle = get_handle(handle_title)
                if handle:
                    app.connect(handle=handle)
                    return app
                else:
                    print("Failed to start Chrome or find window")
                    raise RuntimeError("Chrome not started or window not found")
            except Exception as e:
                print(f"Error starting Chrome: {str(e)}")
                raise

    @staticmethod
    def is_element(window, control_type, title=None, title_re=None):
        try:
            if title:
                if window.child_window(title=title, control_type=control_type).is_visible():
                    return True
            if title_re:
                if window.child_window(title_re=title_re, control_type=control_type).is_visible():
                    return True
        except ElementNotFoundError:
            return False


class Onion(App):
    def __init__(self):
        super().__init__()
        self.app = self.start_app('onion')

    def reg_and_login(self, username, password):
        window = None
        try:
            window = self.app.window(title_re="Onion Mail.*Google Chrome.*")
            window.wait("visible", timeout=20)
            window.set_focus()
            logging.info("Найдено окно браузера с открытой вкладкой почты.")

            if self.is_element(window, title=' INBOX', control_type='Text'):
                buttons = window.descendants(control_type="Button")
                target_btn = None
                for btn in buttons:
                    rect = btn.rectangle()
                    if rect.top == 108 and rect.right == 1682 and rect.bottom == 172:
                        target_btn = btn
                        break
                target_btn.click_input()
                logging.info("Активировано главное меню.")

                try:
                    log_out = window.child_window(control_type='Hyperlink', title='Log out')
                    log_out.wait("visible", timeout=3)
                except Exception as e:
                    print(f"Not found: {e}")
                    log_out = window.child_window(control_type='Hyperlink', title=' Log out')
                    log_out.wait("visible", timeout=3)
                log_out.invoke()
                logging.info("Успешно был произведен выход с прошлой почты.")

            create_acc_btn = window.child_window(title=' Create account', control_type='Hyperlink')
            create_acc_btn.wait("visible", timeout=10)
            create_acc_btn.invoke()
            logging.info("Найдена форма для создания нового аккаунта.")

            name_field = window.child_window(control_type="Edit", auto_id="name")
            name_field.wait("visible", timeout=60)
            name_field.set_text("")
            name_field.type_keys(username, with_spaces=True)
            logging.info("Введено имя пользователя")

            username_field = window.child_window(control_type="Edit", auto_id="username")
            username_field.wait("visible", timeout=10)
            username_field.set_text("")
            username_field.type_keys(username, with_spaces=True)
            logging.info("Введено имя почты")

            password_field = window.child_window(control_type="Edit", auto_id="password")
            password_field.wait("visible", timeout=10)
            password_field.set_text("")
            password_field.type_keys(password, with_spaces=True)
            logging.info("Введен пароль")

            confirm_password_field = window.child_window(control_type="Edit", auto_id="password2")
            confirm_password_field.wait("visible", timeout=10)
            confirm_password_field.set_text("")
            confirm_password_field.type_keys(password, with_spaces=True)
            logging.info("Пароль подтвержден")

            logging.info("Ищем чекбокс...")
            try:
                checkbox = window.child_window(control_type='CheckBox', title=" Agree to terms of service")
                checkbox.wait("visible", timeout=1)
            except Exception:
                checkbox = window.child_window(control_type='CheckBox', title="Agree to terms of service")
                checkbox.wait("visible", timeout=1)
            checkbox.click_input()
            logging.info("Чекбокс активирован")

            create_account_btn = window.child_window(control_type='Button', title='CREATE NEW ACCOUNT')
            create_account_btn.wait("visible", timeout=10)
            create_account_btn.invoke()
            logging.info("Новый аккаунт почты создан")
            time.sleep(5)

            username_field_log = window.child_window(control_type="Edit", auto_id="username")
            username_field_log.wait("visible", timeout=60)
            username_field_log.set_text("")
            username_field_log.type_keys(username, with_spaces=True)
            logging.info("Имя введено")

            password_field_log = window.child_window(control_type="Edit", auto_id="password")
            password_field_log.wait("visible", timeout=60)
            password_field_log.set_text("")
            password_field_log.type_keys(password, with_spaces=True)
            logging.info("Пароль введен")

            try:
                login_btn = window.child_window(control_type="Button", title=' LOG IN')
                login_btn.wait("visible", timeout=1)
            except Exception as e:
                print(f"Not found: {e}")
                login_btn = window.child_window(control_type="Button", title='LOG IN')
                login_btn.wait("visible", timeout=1)
            time.sleep(1)
            login_btn.invoke()
            logging.info("Вход в аккаунт почты выполнен успешно")

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

    def extract_code(self, time_out=5, second_req=False):
        window = None
        attempts = 3
        attempt = 0
        try:
            window = self.app.window(title_re="Onion Mail.*Google Chrome.*")
            window.wait("visible", timeout=20)
            window.set_focus()

            code_element = None
            while attempt < attempts:
                reload_page = window.child_window(title="Перезагрузить", control_type="Button")
                reload_page.wait("visible", timeout=time_out)
                reload_page.invoke()

                if second_req:
                    code_element = window.child_window(title_re=r'.*Dear , Your code is: \d+', control_type='DataItem')
                else:
                    code_element = window.child_window(title_re=r'.*Hello Your code is: \d+', control_type='DataItem')

                if code_element.is_visible():
                    break
                else:
                    time.sleep(time_out)

            text = code_element.window_text()
            code = re.search(r"Your Code - (\d+)", text).group(1)
            print(f"Extracted code: {code}")

            return code
        except ElementNotFoundError as e:
            print(f"ElementNotFoundError in extract_code: {e}")
            window.print_control_identifiers()
            return None
        except Exception as e:
            print(f"General error in extract_code: {e}")
            window.print_control_identifiers()
            return None


class VPN(App):
    def __init__(self):
        super().__init__()
        self.app = self.start_app('vpn')

    def reconnection(self):
        window = None
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


if __name__ == '__main__':
    vpn = VPN()
    vpn.reconnection()
