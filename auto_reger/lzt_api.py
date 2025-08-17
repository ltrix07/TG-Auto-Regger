import requests
from typing import Literal


class LZTAPI:
    ID = None
    USERNAME = None
    BALANCE = None
    EMAIL = None
    ACTIVE_ITEMS = None

    def __init__(self, token=None, token_path=None):
        if not token and not token_path:
            self.token = input("Enter token for Lolzteam market: ")

        if token and not token_path:
            self.token = token
        else:
            with open(token_path, 'r', encoding='utf-8') as f_o:
                self.token = f_o.read().strip()

        me = self.get_me()
        self.ID = me["user"]["user_id"]
        self.USERNAME = me["user"]["username"]
        self.BALANCE = me["user"]["balance"]
        self.EMAIL = me["user"]["user_email"]
        self.ACTIVE_ITEMS = me["user"]["active_items_count"]

        print(f"You log in like: {self.USERNAME}\n"
              f"Account info:\n\n"
              f"ID: {self.ID}\n"
              f"Username: {self.USERNAME}\n"
              f"Email: {self.EMAIL}\n"
              f"Active items: {self.ACTIVE_ITEMS}")

    def get_me(self):
        url = "https://prod-api.lzt.market/me"

        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.token}"
        }

        response = requests.get(url, headers=headers)

        return response.json()

    def get_accounts_list(self, category_id=None, show='active'):
        url = f"https://prod-api.lzt.market/user/orders?user_id={self.ID}&page=100&show={show}"
        if category_id:
            url += f"&category_id={category_id}"

        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.token}"
        }

        response = requests.get(url, headers=headers)

        return response.json()

    def item_bump(self, item_id):
        url = f"https://prod-api.lzt.market/{item_id}/bump"

        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.token}"
        }

        response = requests.post(url, headers=headers)

        return response.json()

    def upload_item(self,
                    title,
                    title_en,
                    price,
                    description,
                    information=None,
                    category_id=24,
                    currency='usd',
                    item_origin='self_registration',
                    extended_guarantee=0,
                    allow_ask_discount='true'):
        url = f"https://prod-api.lzt.market/item/fast-sell?title={title}&title_en={title_en}&price={price}&category_id={category_id}&currency={currency}&item_origin={item_origin}&extended_guarantee={extended_guarantee}&allow_ask_discount={allow_ask_discount}"

        payload = {
            "description": description
        }

        if information:
            payload["information"] = information

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.token}"
        }

        response = requests.post(url, json=payload, headers=headers)

        return response.json()

    def category(self, name: str):
        url = f"https://prod-api.lzt.market/{name}/params"

        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.token}"
        }

        response = requests.get(url, headers=headers)

        return response.json()

    def search_by_category_telegram(
            self,
            page: int = 10,
            pmin: int = None,
            pmax: int = None,
            title: str = None,
            order_by: Literal['price_to_up', 'price_to_down', 'pdate_to_down', 'pdate_to_up', 'pdate_to_down_upload',
            'pdate_to_up_upload', 'edate_to_up', 'edate_to_down', 'ddate_to_up', 'ddate_to_down'] = None,
            tag_id: list = None,
            not_tag_id: list = None,
            origin: list = None,
            not_origin: list = None,
            user_id: int = None,
            no_sold_before: bool = None,
            sold_before: bool = None,
            nsb_by_me: bool = None,
            sb_by_me: bool = None,
            currency: str = None,
            spam: Literal['yes', 'no', 'nomatter'] = None,
            password: Literal['yes', 'no', 'nomatter'] = None,
            premium: Literal['yes', 'no', 'nomatter'] = None,
            country: list = None,
            not_country: list = None
    ):
        url = "https://prod-api.lzt.market/telegram"

        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.token}"
        }

        params = {}
        if page is not None:
            params['page'] = page
        if pmin is not None:
            params['pmin'] = pmin
        if pmax is not None:
            params['pmax'] = pmax
        if title is not None:
            params['title'] = title
        if order_by is not None:
            params['order_by'] = order_by
        if tag_id is not None:
            params['tag_id'] = tag_id
        if not_tag_id is not None:
            params['not_tag_id'] = not_tag_id
        if origin is not None:
            params['origin[]'] = origin
        if not_origin is not None:
            params['not_origin[]'] = not_origin
        if user_id is not None:
            params['user_id'] = user_id
        if no_sold_before is not None:
            params['nsb'] = no_sold_before
        if sold_before is not None:
            params['sb'] = sold_before
        if nsb_by_me is not None:
            params['nsb_by_me'] = nsb_by_me
        if sb_by_me is not None:
            params['sb_by_me'] = sb_by_me
        if currency is not None:
            params['currency'] = currency
        if spam is not None:
            params['spam'] = spam
        if password is not None:
            params['password'] = password
        if premium is not None:
            params['premium'] = premium
        if country is not None:
            params['country[]'] = country
        if not_country is not None:
            params['not_country[]'] = not_country

        response = requests.get(url, headers=headers, params=params)
        return response


if __name__ == '__main__':
    lzt = LZTAPI(token_path=r'C:\Users\Владимир\PycharmProjects\TG-Auto-Reg\lzt_token.txt')
    response = lzt.search_by_category_telegram(
        page=1,
        origin=['self_registration', 'autoreg'],
        currency='usd',
        country=['US'],
        spam='no',
        password='no'
    )

    prices = []

    for item in response.json()['items']:
        print(item)
