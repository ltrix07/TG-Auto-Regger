from auto_reger.sms_api import SMSAPI


def test_check_verif_status():
    sa = SMSAPI(api_key_path=r'C:\Users\Владимир\PycharmProjects\TG-Auto-Reg\sms_activate_api.txt')
    sa.check_verif_status(3602354209)
