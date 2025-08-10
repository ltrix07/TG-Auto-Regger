from auto_reger.emulator_handler import Telegram


def test_start_messaging():
    telegram = Telegram('localhost:5555', 4723)
    print('Connection success!')

    telegram.start()
    print('Telegram start!')

    telegram.click_start_messaging()
    print('Button pressed!')
