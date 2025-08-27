from auto_reger.emulator import Emulator


def test_check_app_installed():
    emulator = Emulator('localhost:5555', 4723)
    print(emulator.check_app_installed('org.telegram.messenger.web'))
