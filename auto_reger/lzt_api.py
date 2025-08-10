import requests


class LZTAPI:
    ID = None
    USERNAME = None
    BALANCE = None
    EMAIL = None
    ACTIVE_ITEMS = None

    def __init__(self, token=None):
        if not token:
            self.token = input("Enter token for Lolzteam market: ")
        else:
            self.token = token

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


if __name__ == '__main__':
    lzt = LZTAPI()
    lzt.get_me()
