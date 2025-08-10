from auto_reger.emulator_handler import Emulator


def test_init_():
    emulator = Emulator('localhost:5555', 4723)
    print(emulator.driver)
