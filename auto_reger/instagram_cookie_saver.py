import json
from mitmproxy import http

# Имя файла для сохранения cookie
COOKIE_FILE = "instagram_cookies.json"


def response(flow: http.HTTPFlow):
    """
    Эта функция вызывается для каждого HTTP-ответа, который проходит через прокси.
    """
    # Проверяем, что ответ пришел с домена Instagram
    if "instagram.com" in flow.request.host:
        print(f"Обнаружен трафик Instagram: {flow.request.url}")

        # Проверяем, что в ответе есть заголовки Set-Cookie
        # Instagram может отправлять куки в разных запросах,
        # например, после успешной авторизации
        if "set-cookie" in flow.response.headers:
            all_cookies = flow.response.headers["set-cookie"]

            # Сохраняем куки
            try:
                # Читаем существующие куки, чтобы не перезаписывать файл
                with open(COOKIE_FILE, "r") as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = []

            # Добавляем новые куки
            data.append({
                "url": flow.request.url,
                "cookies": all_cookies
            })

            # Записываем обновленные данные в файл
            with open(COOKIE_FILE, "w") as f:
                json.dump(data, f, indent=4)

            print(f"✅ Успешно перехвачены и сохранены cookie в файл {COOKIE_FILE}")