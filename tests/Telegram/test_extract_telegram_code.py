from auto_reger.emulator_handler import Telegram


def test_extract_telegram_code():
    telegram = Telegram('localhost:5555')
    telegram.reconnection()
    telegram.extract_telegram_code()
