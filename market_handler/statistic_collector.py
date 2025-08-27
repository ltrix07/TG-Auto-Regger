import logging
import time
from auto_reger.sms_api import SmsApi
from LOLZTEAM.Client import Market
import csv


def statistic_collector():
    sms_activate = SmsApi(service='sms-activate',
                          api_key_path=r'/sms_activate_api.txt')
    sms_grizzly = SmsApi(service='grizzly-sms',
                         api_key_path=r'/grizzly_sms_api.txt')
    with open(r'/lzt_token.txt', 'rb') as file:
        token = bytes.decode(file.read())

    market = Market(token=token)

    country_map_eng_to_rus_and_code = {
        'Afghanistan': {'rus': 'Афганистан', 'code': 'AF'},
        'Albania': {'rus': 'Албания', 'code': 'AL'},
        'Algeria': {'rus': 'Алжир', 'code': 'DZ'},
        'Andorra': {'rus': 'Андорра', 'code': 'AD'},
        'Angola': {'rus': 'Ангола', 'code': 'AO'},
        'Antigua and Barbuda': {'rus': 'Антигуа и Барбуда', 'code': 'AG'},
        'Argentina': {'rus': 'Аргентина', 'code': 'AR'},
        'Armenia': {'rus': 'Армения', 'code': 'AM'},
        'Australia': {'rus': 'Австралия', 'code': 'AU'},
        'Austria': {'rus': 'Австрия', 'code': 'AT'},
        'Azerbaijan': {'rus': 'Азербайджан', 'code': 'AZ'},
        'Bahamas': {'rus': 'Багамы', 'code': 'BS'},
        'Bahrain': {'rus': 'Бахрейн', 'code': 'BH'},
        'Bangladesh': {'rus': 'Бангладеш', 'code': 'BD'},
        'Barbados': {'rus': 'Барбадос', 'code': 'BB'},
        'Belarus': {'rus': 'Беларусь', 'code': 'BY'},
        'Belgium': {'rus': 'Бельгия', 'code': 'BE'},
        'Belize': {'rus': 'Белиз', 'code': 'BZ'},
        'Benin': {'rus': 'Бенин', 'code': 'BJ'},
        'Bhutan': {'rus': 'Бутан', 'code': 'BT'},
        'Bolivia': {'rus': 'Боливия', 'code': 'BO'},
        'Bosnia and Herzegovina': {'rus': 'Босния и Герцеговина', 'code': 'BA'},
        'Botswana': {'rus': 'Ботсвана', 'code': 'BW'},
        'Brazil': {'rus': 'Бразилия', 'code': 'BR'},
        'Brunei': {'rus': 'Бруней', 'code': 'BN'},
        'Bulgaria': {'rus': 'Болгария', 'code': 'BG'},
        'Burkina Faso': {'rus': 'Буркина-Фасо', 'code': 'BF'},
        'Burundi': {'rus': 'Бурунди', 'code': 'BI'},
        'Cambodia': {'rus': 'Камбоджа', 'code': 'KH'},
        'Cameroon': {'rus': 'Камерун', 'code': 'CM'},
        'Canada': {'rus': 'Канада', 'code': 'CA'},
        'Cape Verde': {'rus': 'Кабо-Верде', 'code': 'CV'},
        'Central African Republic': {'rus': 'Центральноафриканская Республика', 'code': 'CF'},
        'Chad': {'rus': 'Чад', 'code': 'TD'},
        'Chile': {'rus': 'Чили', 'code': 'CL'},
        'China': {'rus': 'Китай', 'code': 'CN'},
        'Colombia': {'rus': 'Колумбия', 'code': 'CO'},
        'Comoros': {'rus': 'Коморы', 'code': 'KM'},
        'Congo (Brazzaville)': {'rus': 'Конго (Браззавиль)', 'code': 'CG'},
        'Congo (Kinshasa)': {'rus': 'Конго (Киншаса)', 'code': 'CD'},
        'Costa Rica': {'rus': 'Коста-Рика', 'code': 'CR'},
        'Croatia': {'rus': 'Хорватия', 'code': 'HR'},
        'Cuba': {'rus': 'Куба', 'code': 'CU'},
        'Cyprus': {'rus': 'Кипр', 'code': 'CY'},
        'Czech Republic': {'rus': 'Чехия', 'code': 'CZ'},
        'Denmark': {'rus': 'Дания', 'code': 'DK'},
        'Djibouti': {'rus': 'Джибути', 'code': 'DJ'},
        'Dominica': {'rus': 'Доминика', 'code': 'DM'},
        'Dominican Republic': {'rus': 'Доминиканская Республика', 'code': 'DO'},
        'East Timor': {'rus': 'Восточный Тимор', 'code': 'TL'},
        'Ecuador': {'rus': 'Эквадор', 'code': 'EC'},
        'Egypt': {'rus': 'Египет', 'code': 'EG'},
        'El Salvador': {'rus': 'Сальвадор', 'code': 'SV'},
        'Equatorial Guinea': {'rus': 'Экваториальная Гвинея', 'code': 'GQ'},
        'Eritrea': {'rus': 'Эритрея', 'code': 'ER'},
        'Estonia': {'rus': 'Эстония', 'code': 'EE'},
        'Eswatini': {'rus': 'Эсватини', 'code': 'SZ'},
        'Ethiopia': {'rus': 'Эфиопия', 'code': 'ET'},
        'Fiji': {'rus': 'Фиджи', 'code': 'FJ'},
        'Finland': {'rus': 'Финляндия', 'code': 'FI'},
        'France': {'rus': 'Франция', 'code': 'FR'},
        'Gabon': {'rus': 'Габон', 'code': 'GA'},
        'Gambia': {'rus': 'Гамбия', 'code': 'GM'},
        'Georgia': {'rus': 'Грузия', 'code': 'GE'},
        'Germany': {'rus': 'Германия', 'code': 'DE'},
        'Ghana': {'rus': 'Гана', 'code': 'GH'},
        'Greece': {'rus': 'Греция', 'code': 'GR'},
        'Grenada': {'rus': 'Гренада', 'code': 'GD'},
        'Guatemala': {'rus': 'Гватемала', 'code': 'GT'},
        'Guinea': {'rus': 'Гвинея', 'code': 'GN'},
        'Guinea-Bissau': {'rus': 'Гвинея-Бисау', 'code': 'GW'},
        'Guyana': {'rus': 'Гайана', 'code': 'GY'},
        'Haiti': {'rus': 'Гаити', 'code': 'HT'},
        'Honduras': {'rus': 'Гондурас', 'code': 'HN'},
        'Hungary': {'rus': 'Венгрия', 'code': 'HU'},
        'Iceland': {'rus': 'Исландия', 'code': 'IS'},
        'India': {'rus': 'Индия', 'code': 'IN'},
        'Indonesia': {'rus': 'Индонезия', 'code': 'ID'},
        'Iran': {'rus': 'Иран', 'code': 'IR'},
        'Iraq': {'rus': 'Ирак', 'code': 'IQ'},
        'Ireland': {'rus': 'Ирландия', 'code': 'IE'},
        'Israel': {'rus': 'Израиль', 'code': 'IL'},
        'Italy': {'rus': 'Италия', 'code': 'IT'},
        'Ivory Coast': {'rus': 'Кот-д\'Ивуар', 'code': 'CI'},
        'Jamaica': {'rus': 'Ямайка', 'code': 'JM'},
        'Japan': {'rus': 'Япония', 'code': 'JP'},
        'Jordan': {'rus': 'Иордания', 'code': 'JO'},
        'Kazakhstan': {'rus': 'Казахстан', 'code': 'KZ'},
        'Kenya': {'rus': 'Кения', 'code': 'KE'},
        'Kiribati': {'rus': 'Кирибати', 'code': 'KI'},
        'Kosovo': {'rus': 'Косово', 'code': 'XK'},
        'Kuwait': {'rus': 'Кувейт', 'code': 'KW'},
        'Kyrgyzstan': {'rus': 'Киргизия', 'code': 'KG'},
        'Laos': {'rus': 'Лаос', 'code': 'LA'},
        'Latvia': {'rus': 'Латвия', 'code': 'LV'},
        'Lebanon': {'rus': 'Ливан', 'code': 'LB'},
        'Lesotho': {'rus': 'Лесото', 'code': 'LS'},
        'Liberia': {'rus': 'Либерия', 'code': 'LR'},
        'Libya': {'rus': 'Ливия', 'code': 'LY'},
        'Liechtenstein': {'rus': 'Лихтенштейн', 'code': 'LI'},
        'Lithuania': {'rus': 'Литва', 'code': 'LT'},
        'Luxembourg': {'rus': 'Люксембург', 'code': 'LU'},
        'Madagascar': {'rus': 'Мадагаскар', 'code': 'MG'},
        'Malawi': {'rus': 'Малави', 'code': 'MW'},
        'Malaysia': {'rus': 'Малайзия', 'code': 'MY'},
        'Maldives': {'rus': 'Мальдивы', 'code': 'MV'},
        'Mali': {'rus': 'Мали', 'code': 'ML'},
        'Malta': {'rus': 'Мальта', 'code': 'MT'},
        'Marshall Islands': {'rus': 'Маршалловы Острова', 'code': 'MH'},
        'Mauritania': {'rus': 'Мавритания', 'code': 'MR'},
        'Mauritius': {'rus': 'Маврикий', 'code': 'MU'},
        'Mexico': {'rus': 'Мексика', 'code': 'MX'},
        'Micronesia': {'rus': 'Микронезия', 'code': 'FM'},
        'Moldova': {'rus': 'Молдова', 'code': 'MD'},
        'Monaco': {'rus': 'Монако', 'code': 'MC'},
        'Mongolia': {'rus': 'Монголия', 'code': 'MN'},
        'Montenegro': {'rus': 'Черногория', 'code': 'ME'},
        'Morocco': {'rus': 'Марокко', 'code': 'MA'},
        'Mozambique': {'rus': 'Мозамбик', 'code': 'MZ'},
        'Myanmar': {'rus': 'Мьянма', 'code': 'MM'},
        'Namibia': {'rus': 'Намибия', 'code': 'NA'},
        'Nauru': {'rus': 'Науру', 'code': 'NR'},
        'Nepal': {'rus': 'Непал', 'code': 'NP'},
        'Netherlands': {'rus': 'Нидерланды', 'code': 'NL'},
        'New Zealand': {'rus': 'Новая Зеландия', 'code': 'NZ'},
        'Nicaragua': {'rus': 'Никарагуа', 'code': 'NI'},
        'Niger': {'rus': 'Нигер', 'code': 'NE'},
        'Nigeria': {'rus': 'Нигерия', 'code': 'NG'},
        'North Korea': {'rus': 'Северная Корея', 'code': 'KP'},
        'North Macedonia': {'rus': 'Северная Македония', 'code': 'MK'},
        'Norway': {'rus': 'Норвегия', 'code': 'NO'},
        'Oman': {'rus': 'Оман', 'code': 'OM'},
        'Pakistan': {'rus': 'Пакистан', 'code': 'PK'},
        'Palau': {'rus': 'Палау', 'code': 'PW'},
        'Palestine': {'rus': 'Палестина', 'code': 'PS'},
        'Panama': {'rus': 'Панама', 'code': 'PA'},
        'Papua New Guinea': {'rus': 'Папуа — Новая Гвинея', 'code': 'PG'},
        'Paraguay': {'rus': 'Парагвай', 'code': 'PY'},
        'Peru': {'rus': 'Перу', 'code': 'PE'},
        'Philippines': {'rus': 'Филиппины', 'code': 'PH'},
        'Poland': {'rus': 'Польша', 'code': 'PL'},
        'Portugal': {'rus': 'Португалия', 'code': 'PT'},
        'Qatar': {'rus': 'Катар', 'code': 'QA'},
        'Romania': {'rus': 'Румыния', 'code': 'RO'},
        'Russia': {'rus': 'Россия', 'code': 'RU'},
        'Rwanda': {'rus': 'Руанда', 'code': 'RW'},
        'Saint Kitts and Nevis': {'rus': 'Сент-Китс и Невис', 'code': 'KN'},
        'Saint Lucia': {'rus': 'Сент-Люсия', 'code': 'LC'},
        'Saint Vincent and the Grenadines': {'rus': 'Сент-Винсент и Гренадины', 'code': 'VC'},
        'Samoa': {'rus': 'Самоа', 'code': 'WS'},
        'San Marino': {'rus': 'Сан-Марино', 'code': 'SM'},
        'Sao Tome and Principe': {'rus': 'Сан-Томе и Принсипи', 'code': 'ST'},
        'Saudi Arabia': {'rus': 'Саудовская Аравия', 'code': 'SA'},
        'Senegal': {'rus': 'Сенегал', 'code': 'SN'},
        'Serbia': {'rus': 'Сербия', 'code': 'RS'},
        'Seychelles': {'rus': 'Сейшельские Острова', 'code': 'SC'},
        'Sierra Leone': {'rus': 'Сьерра-Леоне', 'code': 'SL'},
        'Singapore': {'rus': 'Сингапур', 'code': 'SG'},
        'Slovakia': {'rus': 'Словакия', 'code': 'SK'},
        'Slovenia': {'rus': 'Словения', 'code': 'SI'},
        'Solomon Islands': {'rus': 'Соломоновы Острова', 'code': 'SB'},
        'Somalia': {'rus': 'Сомали', 'code': 'SO'},
        'South Africa': {'rus': 'Южно-Африканская Республика', 'code': 'ZA'},
        'South Korea': {'rus': 'Южная Корея', 'code': 'KR'},
        'South Sudan': {'rus': 'Южный Судан', 'code': 'SS'},
        'Spain': {'rus': 'Испания', 'code': 'ES'},
        'Sri Lanka': {'rus': 'Шри-Ланка', 'code': 'LK'},
        'Sudan': {'rus': 'Судан', 'code': 'SD'},
        'Suriname': {'rus': 'Суринам', 'code': 'SR'},
        'Sweden': {'rus': 'Швеция', 'code': 'SE'},
        'Switzerland': {'rus': 'Швейцария', 'code': 'CH'},
        'Syria': {'rus': 'Сирия', 'code': 'SY'},
        'Taiwan': {'rus': 'Тайвань', 'code': 'TW'},
        'Tajikistan': {'rus': 'Таджикистан', 'code': 'TJ'},
        'Tanzania': {'rus': 'Танзания', 'code': 'TZ'},
        'Thailand': {'rus': 'Таиланд', 'code': 'TH'},
        'Togo': {'rus': 'Того', 'code': 'TG'},
        'Tonga': {'rus': 'Тонга', 'code': 'TO'},
        'Trinidad and Tobago': {'rus': 'Тринидад и Тобаго', 'code': 'TT'},
        'Tunisia': {'rus': 'Тунис', 'code': 'TN'},
        'Turkey': {'rus': 'Турция', 'code': 'TR'},
        'Turkmenistan': {'rus': 'Туркменистан', 'code': 'TM'},
        'Tuvalu': {'rus': 'Тувалу', 'code': 'TV'},
        'Uganda': {'rus': 'Уганда', 'code': 'UG'},
        'Ukraine': {'rus': 'Украина', 'code': 'UA'},
        'United Arab Emirates': {'rus': 'Объединённые Арабские Эмираты', 'code': 'AE'},
        'United Kingdom': {'rus': 'Великобритания', 'code': 'GB'},
        'United States': {'rus': 'Соединённые Штаты', 'code': 'US'},
        'United States virt': {'rus': 'Соединённые Штаты', 'code': 'US'},
        'Uruguay': {'rus': 'Уругвай', 'code': 'UY'},
        'Uzbekistan': {'rus': 'Узбекистан', 'code': 'UZ'},
        'Vanuatu': {'rus': 'Вануату', 'code': 'VU'},
        'Vatican City': {'rus': 'Ватикан', 'code': 'VA'},
        'Venezuela': {'rus': 'Венесуэла', 'code': 'VE'},
        'Vietnam': {'rus': 'Вьетнам', 'code': 'VN'},
        'Yemen': {'rus': 'Йемен', 'code': 'YE'},
        'Zambia': {'rus': 'Замбия', 'code': 'ZM'},
        'Zimbabwe': {'rus': 'Зимбабве', 'code': 'ZW'}
    }

    countries_activate = sms_activate.getCountries()
    countries_grizzly = sms_grizzly.getCountries()
    unique_eng_countries = set()
    for countries in [countries_activate, countries_grizzly]:
        for country_data in countries.values():
            if 'eng' in country_data:
                unique_eng_countries.add(country_data['eng'])

    data = []
    for eng_country in sorted(unique_eng_countries):
        country_info = country_map_eng_to_rus_and_code.get(eng_country)
        if not country_info:
            continue
        rus_country = country_info['rus']
        country_code = country_info['code']

        # Get prices from suppliers, handle errors
        price_activate = None
        price_grizzly = None
        count_activate = None
        count_grizzly = None
        try:
            for values in sms_activate.get_price('tg', eng_country).values():
                price_activate = values['tg']['cost']
                count_activate = values['tg']['count']
        except Exception:
            pass
        try:
            for values in sms_grizzly.get_price('tg', eng_country).values():
                price_grizzly = values['tg']['cost'] / 79.86
                count_grizzly = values['tg']['count']
        except Exception:
            pass

        prices = []
        page = 1

        items_qty = 0
        while page <= 5:
            response = market.categories.telegram.get(
                page=page,
                origin=['self_registration', 'autoreg'],
                currency='usd',
                spam='no',
                password='no',
                country=[country_code]
            )
            if response.status_code != 200:
                print("Превышено количество запросов. Ждем указанное время...")
                time.sleep(15 * 60)
                break
            items = response.json().get('items', [])
            if not items:
                break
            for item in items:
                prices.append(item['price'])

            items_qty += len(items)
            page += 1

        market_min = min(prices) if prices else None
        market_max = max(prices) if prices else None
        market_avg = sum(prices) / len(prices) if prices else None

        margin_activate = market_avg - price_activate if market_avg is not None and price_activate is not None else None
        margin_activate_min = market_min - price_activate if market_min is not None and price_activate is not None else None
        margin_activate_max = market_max - price_activate if market_max is not None and price_activate is not None else None

        margin_grizzly = market_avg - price_grizzly if market_avg is not None and price_grizzly is not None else None
        margin_grizzly_min = market_min - price_grizzly if market_min is not None and price_grizzly is not None else None
        margin_grizzly_max = market_max - price_grizzly if market_max is not None and price_grizzly is not None else None

        margin = None
        margin_min = None
        margin_max = None
        better_supplier = None
        if margin_activate and margin_grizzly:
            margin = margin_grizzly if margin_grizzly > margin_activate else margin_activate
            margin_min = margin_grizzly_min if margin_grizzly_min > margin_activate_min else margin_activate_min
            margin_max = margin_grizzly_max if margin_grizzly_max > margin_activate_max else margin_activate_max
            better_supplier = 'grizzly-sms' if margin_grizzly > margin_activate else 'sms-activate'
        elif margin_activate and not margin_grizzly:
            margin = margin_activate
            margin_min = margin_activate_min
            margin_max = margin_activate_max
            better_supplier = 'sms-activate'
        elif not margin_activate and margin_grizzly:
            margin = margin_grizzly
            margin_min = margin_grizzly_min
            margin_max = margin_grizzly_max
            better_supplier = 'grizzly-sms'

        info = {
            'Country_Eng': eng_country,
            'Country_Rus': rus_country,
            'Price_Activate': round(price_activate, 2) if price_activate else None,
            'Price_Grizzly': round(price_grizzly, 2) if price_grizzly else None,
            'Qty_Activate': count_activate,
            'Qty_Grizzly': count_grizzly,
            'Market_Min': round(market_min, 2) if market_min else None,
            'Market_Max': round(market_max, 2) if market_max else None,
            'Market_Avg': round(market_avg, 2) if market_avg else None,
            'Margin': round(margin, 2) if margin else None,
            'Margin_Max': round(margin_max, 2) if margin_max else None,
            'Margin_Min': round(margin_min, 2) if margin_min else None,
            'Better_Supplier': better_supplier,
            'Items_Qty': items_qty
        }
        data.append(info)
        print(f"{'-' * 40}")
        print(f"Обработана страна: {eng_country}")
        print(f"{'-' * 40}")
        print(f"{'Название (Eng)':<20}: {info['Country_Eng']}")
        print(f"{'Название (Rus)':<20}: {info['Country_Rus']}")
        print(
            f"{'Цена Activate':<20}: {info['Price_Activate'] if info['Price_Activate'] is not None else 'N/A'}")
        print(
            f"{'Цена Grizzly':<20}: {info['Price_Grizzly'] if info['Price_Grizzly'] is not None else 'N/A'}")
        print(f"{'Рынок (Мин)':<20}: {info['Market_Min'] if info['Market_Min'] is not None else 'N/A'}")
        print(
            f"{'Рынок (Макс)':<20}: {info['Market_Max'] if info['Market_Max'] is not None else 'N/A'}")
        print(
            f"{'Рынок (Сред)':<20}: {info['Market_Avg'] if info['Market_Avg'] is not None else 'N/A'}")
        print(
            f"{'Маржа усредненная':<20}: {info['Margin'] if info['Margin'] is not None else 'N/A'}")
        print(
            f"{'Маржа минимальная':<20}: {info['Margin_Min'] if info['Margin_Min'] is not None else 'N/A'}")
        print(
            f"{'Маржа максимальная':<20}: {info['Margin_Max'] if info['Margin_Max'] is not None else 'N/A'}")
        print(
            f"{'Лучший поставщик':<20}: {info['Better_Supplier'] if info['Better_Supplier'] is not None else 'N/A'}")
        print(f"{'Количество':<20}: {info['Items_Qty']}")
        print(f"{'-' * 40}\n")

    file_name = 'market_stats_15.08.csv'
    # Write to CSV
    with open(file_name, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Country_Eng', 'Country_Rus', 'Price_Activate', 'Price_Grizzly',
                                               'Qty_Activate', 'Qty_Grizzly', 'Market_Min', 'Market_Max',
                                               'Market_Avg', 'Margin', 'Margin_Min', 'Margin_Max',
                                               'Better_Supplier', 'Items_Qty'])
        writer.writeheader()
        writer.writerows(data)

    logging.info(f"Данные было записано в файл {file_name}")


statistic_collector()
