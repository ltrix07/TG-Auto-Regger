from LOLZTEAM.Client import Market
import argparse
from datetime import datetime
from utils import read_json, write_json
from typing import Literal
import csv


with open('lzt_token.txt', 'rb') as file:
    TOKEN = bytes.decode(file.read())

market = Market(token=TOKEN)


def get_top_sellers(
        pages_count: int,
        country: list = None,
        origin: list = None,
        currency: str = 'usd',
        spam: str = 'no',
        password: str = 'no'
):
    page = 1

    full_items_data = []
    while page <= pages_count:
        response = market.categories.telegram.get(
            page=page,
            country=country,
            show='active',
            origin=origin,
            order_by='pdate_to_down',
            currency=currency,
            spam=spam,
            password=password,
        )
        items = response.json().get('items', [])
        if not items:
            break

        for item in items:
            full_items_data.append(item)

        print(f"Собраны данные со страницы {page}")
        page += 1

    sellers = {}
    for item in full_items_data:
        seller_obj = item['seller']

        if not seller_obj['username'] in sellers:
            sellers[seller_obj['username']] = {
                'seller_id': seller_obj['user_id'],
                'sold_items_count': seller_obj['sold_items_count'],
                'active_items_count': seller_obj['active_items_count'],
                'seller_items_in_search': 1
            }
        else:
            sellers[seller_obj['username']]['seller_items_in_search'] += 1

    write_json(sellers, f'{datetime.now().strftime("%Y-%m-%d")}_sellers.json')

    with open(f'{datetime.now().strftime("%Y-%m-%d")}_sellers_{country[0]}.csv', mode='w', newline='', encoding='utf-8') as csv_f:
        writer = csv.writer(csv_f)

        headers = ['username']
        for key in sellers[next(iter(sellers))].keys():
            headers.append(key)

        writer.writerow(headers)

        for username, data in sellers.items():
            row = [username]
            writer.writerow(row + [data[cell] for cell in headers if cell != 'username'])


if __name__ == '__main__':
    get_top_sellers(
        pages_count=10,
        country=['CY'],
        origin=['autoreg'],
    )
