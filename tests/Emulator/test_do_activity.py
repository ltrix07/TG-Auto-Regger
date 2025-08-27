from auto_reger.emulator import Emulator


def test_do_activity():
    emulator = Emulator('localhost:5555', 4723)
    emulator.do_activity('org.telegram.messenger.web',
                         'org.telegram.messenger.web/org.telegram.ui.LaunchActivity')
