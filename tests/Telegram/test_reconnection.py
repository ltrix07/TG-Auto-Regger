from auto_reger.emulator_handler import Telegram
from selenium.webdriver.common.by import By


def test_reconnection():
    telegram = Telegram('localhost:5555', 4723)
    telegram.reconnection()
    print(telegram.check_element(By.XPATH, '//android.widget.TextView[@text="Check your Telegram messages"]'))

