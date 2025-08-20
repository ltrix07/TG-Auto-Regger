from smsactivate.api import SMSActivateAPI
from datetime import datetime, timedelta
import requests
import time
import json
import os
import logging


logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')


def save_activation_to_json(activation_id, phone):
    """Сохраняет activation_id, phone и время запроса в JSON."""
    json_file = 'activations.json'
    data = []
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            data = json.load(f)

    data.append({
        'activation_id': activation_id,
        'phone': phone,
        'request_time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    })

    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)
    logging.info(f"Saved activation_id {activation_id} to {json_file}")


def can_set_status_8(activation_id):
    """Проверяет, прошло ли 2 минуты с момента запроса activation_id."""
    json_file = 'activations.json'
    if not os.path.exists(json_file):
        return False

    with open(json_file, 'r') as f:
        data = json.load(f)

    for entry in data:
        if entry['activation_id'] == activation_id:
            request_time = datetime.strptime(entry['request_time'], '%Y-%m-%dT%H:%M:%S')
            if datetime.now() - request_time >= timedelta(minutes=2):
                return True
            return False
    return False


def remove_activation_from_json(activation_id):
    """Удаляет activation_id из JSON после установки статуса."""
    json_file = 'activations.json'
    if not os.path.exists(json_file):
        return

    with open(json_file, 'r') as f:
        data = json.load(f)

    data = [entry for entry in data if entry['activation_id'] != activation_id]

    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)
    logging.info(f"Removed activation_id {activation_id} from {json_file}")


class SmsApi(SMSActivateAPI):
    def __init__(self, service, api_key=None, api_key_path=None):
        if not api_key and not api_key_path:
            raise AttributeError("Вы должны указать либо api_key либо api_key_path в качестве параметра.")
        if not api_key and api_key_path:
            with open(api_key_path, 'r', encoding='utf-8') as f_o:
                api_key = f_o.read().strip()
                print(api_key)

        if service == 'sms-activate':
            self.api_url = 'https://api.sms-activate.ae/stubs/handler_api.php'
        if service == 'grizzly-sms':
            self.api_url = 'https://api.grizzlysms.com/stubs/handler_api.php'

        super().__init__(api_key, self.api_url)

    def getStatusV2(self, id_=None):
        payload = {'api_key': self.api_key, 'action': 'getStatusV2'}
        if id_:
            payload['id'] = id_
        response = requests.get(self.api_url, params=payload)
        return response.json()

    def _get_country_id(self, country):
        if country == 'USA' and 'grizzlysms' in self.api_url:
            country = 'United States virt'
        countries = self.getCountries()
        for allow_country in countries:
            if countries[allow_country]['eng'] == country:
                return allow_country

    def qty_of_numbers(self, service, country):
        country_id = self._get_country_id(country)
        numbers_status = self.getNumbersStatus(country_id)
        return numbers_status[service]

    def verification_number(self, service, country, max_price=None):
        country_id = self._get_country_id(country)
        number_data = self.getNumberV2(service=service, country=int(country_id), maxPrice=max_price)

        return number_data

    def check_verif_status(self, activation_id, timeout=300):
        print('Waiting code...')
        waiting_times = 0
        while waiting_times <= timeout:
            if 'sms-activate' in self.api_url:
                activation_status = self.getStatusV2(activation_id)
                print(activation_status)
                if activation_status['sms']:
                    return activation_status['sms']['code']

            if 'grizzlysms' in self.api_url:
                activation_status = self.getStatus(activation_id)
                print(activation_status)
                if 'STATUS_OK' in activation_status:
                    return activation_status.split(':')[-1]

            time.sleep(5)
            waiting_times += 5

        self.setStatus(activation_id, status=8)
        print('Сообщение не было получено')

    def get_price(self, service, country):
        country_id = self._get_country_id(country)
        resp = self.getPrices(service, country_id)
        return resp


if __name__ == '__main__':
    sms = SmsApi(service='sms-activate', api_key_path=r'C:\Users\Владимир\PycharmProjects\TG-Auto-Reg\sms_activate_api.txt')
    status = sms.get_price('tg', 'Australia')
    print(status)
