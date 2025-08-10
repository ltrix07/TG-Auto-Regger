from auto_reger.emulator_handler import Telegram


def test_press_on_chat_with_telegram():
    telegram = Telegram('localhost:5555')
    telegram.reconnection()
    telegram.click_on_chat_with_telegram()
