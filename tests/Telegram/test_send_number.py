from auto_reger.emulator import Telegram
import random
import time


def test_send_number():
    telegram = Telegram('localhost:5555', 4723)
    telegram.start()
    time.sleep(random.uniform(0.5, 1.5))
    telegram.click_start_messaging()
    time.sleep(random.uniform(0.5, 1.5))
    telegram.click_continue_second_windows()
    time.sleep(random.uniform(0.5, 1.5))
    telegram.click_allow_btn()
    time.sleep(random.uniform(0.5, 1.5))
    telegram.send_number('16185858722')
