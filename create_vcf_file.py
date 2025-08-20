import json
import os
import logging
import subprocess


logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def collect_contacts_from_json(folder_path='./sessions/JSON', processed_file='processed_phones.json'):
    contacts = []
    processed_phones = set()

    # Загрузка уже проработанных номеров, если файл существует
    if os.path.exists(processed_file):
        try:
            with open(processed_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:  # Проверяем, не пустой ли файл
                    processed_phones = set(json.loads(content))
                else:
                    processed_phones = set()  # Если файл пуст, инициализируем пустым множеством
        except json.JSONDecodeError:
            print(f"Ошибка: Файл {processed_file} содержит некорректный JSON. Инициализируем пустой список.")
            processed_phones = set()

    # Сканирование папки
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            phone_number = filename.replace('.json', '')  # Извлечение номера из имени файла
            if phone_number in processed_phones:
                continue  # Пропуск дубликата

            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    contact = {
                        "name": f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                        "phone": data.get('phone_number', phone_number)
                    }
                    contacts.append(contact)

                # Добавление в проработанные
                processed_phones.add(phone_number)
            except json.JSONDecodeError:
                print(f"Ошибка: Файл {file_path} содержит некорректный JSON. Пропускаем.")
                continue

    # Сохранение обновлённого списка проработанных номеров
    with open(processed_file, 'w', encoding='utf-8') as f:
        json.dump(list(processed_phones), f)

    return contacts


def create_vcf_file(contacts, filename="contacts.vcf", remote_update=False):
    # Создание файла .vcf
    with open(filename, "w", encoding="utf-8") as f:
        for contact in contacts:
            f.write("BEGIN:VCARD\n")
            f.write("VERSION:3.0\n")
            f.write(f"N:{contact['name']};;;\n")
            f.write(f"FN:{contact['name']}\n")
            f.write(f"TEL;CELL:{contact['phone']}\n")
            if 'email' in contact:
                f.write(f"EMAIL:{contact['email']}\n")
            f.write("END:VCARD\n")
    logging.info(f"Файл {filename} успешно создан")

    # Передача файла на эмулятор, если remote_update=True
    if remote_update:
        cmd = r'adb push contacts.vcf /sdcard/Download/'
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()

        if process.returncode != 0 or error:
            logging.error(f"Ошибка при выполнении adb push: {error.decode('utf-8')}")
            raise RuntimeError(f"ADB push failed: {error.decode('utf-8')}")
        else:
            logging.info(f"ADB push успешно выполнен: {output.decode('utf-8')}")

    return True


if __name__ == "__main__":
    contacts = collect_contacts_from_json()
    create_vcf_file(contacts, "contacts.vcf", remote_update=True)
