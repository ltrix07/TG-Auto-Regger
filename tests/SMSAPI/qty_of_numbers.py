from auto_reger.sms_api import SmsApi


def qty_of_numbers():
    sa = SmsApi(api_key_path=r'C:\Users\Владимир\PycharmProjects\TG-Auto-Reg\sms_activate_api.txt')
    print(sa.qty_of_numbers('tg', 'USA'))


qty_of_numbers()
