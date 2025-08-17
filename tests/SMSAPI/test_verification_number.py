from auto_reger.sms_api import SmsApi


def test_verification_number():
    sa = SmsApi(api_key_path=r'C:\Users\Владимир\PycharmProjects\TG-Auto-Reg\sms_activate_api.txt')
    num_data = sa.verification_number('tg', 'USA', 'false')
    print(num_data)
