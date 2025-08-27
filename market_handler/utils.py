import json


def read_json(path):
    with open(path, 'r', encoding='utf-8') as f_o:
        return json.load(f_o)


def write_json(obj, path):
    with open(path, 'w', encoding='utf-8') as f_o:
        return json.dump(obj, f_o, indent=4)
