from auto_reger.emulator_handler import Telegram


def test_account_log_out():
    telegram = Telegram('localhost:5555')
    telegram.reconnection()
    telegram.account_log_out()