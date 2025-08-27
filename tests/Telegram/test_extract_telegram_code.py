from auto_reger.emulator import Telegram


def test_extract_telegram_code():
    telegram = Telegram('localhost:5555')
    telegram.reconnection()
    telegram.extract_telegram_code()
