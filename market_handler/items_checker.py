import time
import schedule
from market import market, get_my_accounts


def main():
    items = {}
    my_accs = get_my_accounts(
        category_id=24,
        show='active',
        origin=None,
        spam='yes',
        country_code=None,
        order_by='pdate_to_up'
    )
    if 'errors' in my_accs:
        raise Exception(f"Can't get the items with error: {my_accs['errors']}")

    for item in my_accs:
        items[item['item_id']] = {
            'auth_key': item['loginData']['login'],
            'dc_id': item['loginData']['password']
        }

    for item_id, log_data in items.items():
        check_status = market.publishing.check(
            item_id=item_id,
            login=log_data['auth_key'],
            password=log_data['dc_id'],
            proxy_random=True,
            extra={'checkChannels': True, 'checkSpam': True}
        ).json()
        if 'errors' in check_status:
            print(f'Item {item_id} can\'t be check with error: {check_status["errors"]}')
        elif check_status['status'] == 'ok':
            print(f"Item {item_id} check successful!")


if __name__ == '__main__':
    schedule.every().day.at("03:00").do(main)

    while True:
        schedule.run_pending()
        time.sleep(1)
