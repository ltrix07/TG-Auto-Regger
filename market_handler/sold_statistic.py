import json
import time
import schedule
from datetime import datetime as dt
from datetime import timezone
from collections import Counter, defaultdict
from market import market


def get_all_payment_invoice():
    page = 1
    invoices = []
    offset_seconds = None
    while True:
        response = market.payments.history(
            page=page,
            operation_type='sold_item',
            show_payment_stats=True
        ).json()
        for order_data in response['payments'].values():
            invoices.append(order_data)

        if not offset_seconds:
            server_date = dt.fromtimestamp(response['system_info']['time'], tz=timezone.utc).replace(tzinfo=None)
            offset_seconds = (dt.now() - server_date).total_seconds()

        if response['hasNextPage'] is False:
            break
        page += 1

    return invoices, offset_seconds


def count_by_hour(invoices, offset_seconds):
    sales_by_hour = Counter()
    amount_by_hour = defaultdict(float)

    offset_hours = int(round(offset_seconds / 3600))

    for inv in invoices:
        date = dt.fromtimestamp(inv['operation_date'], tz=timezone.utc)
        hour = int((date.hour + offset_hours) % 24)
        sales_by_hour[hour] += 1
        amount_by_hour[hour] += float(inv['incoming_sum'])

    return sales_by_hour, amount_by_hour


def format_and_save_data(sales_count, total_amount, limit=5):
    """
    Форматирует данные, сортирует их по количеству продаж и сохраняет в файл.
    """
    today_date = dt.now().strftime("%Y-%m-%d")
    file_name = f"{today_date}_sales_report.json"

    # Создаем список кортежей (час, количество продаж, общая сумма)
    combined_data = []
    for hour, count in sales_count.items():
        amount = total_amount.get(hour, 0.0)
        combined_data.append({
            "hour": hour,
            "sales_count": count,
            "total_amount": amount
        })

    # Сортируем список по количеству продаж в порядке убывания
    sorted_data = sorted(combined_data, key=lambda x: x['sales_count'], reverse=True)

    try:
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(sorted_data[:limit], f, ensure_ascii=False, indent=4)
        print(f"Data has been sorted and saved to file: {file_name}")
    except IOError as e:
        print(f"Error with file saving: {e}")

    return sorted_data[:limit]


def collect_statistic():
    invoices, offset = get_all_payment_invoice()
    sales_count, total_amount = count_by_hour(invoices, offset)
    format_and_save_data(sales_count, total_amount)


if __name__ == '__main__':
    schedule.every(3).days.do(collect_statistic)

    while True:
        schedule.run_pending()
        time.sleep(1)
