import json
import os

CONFIG_FILE = "config.json"


def load_config():

    if not os.path.exists(CONFIG_FILE):
        return {}

    if os.path.getsize(CONFIG_FILE) == 0:
        return {}

    with open(CONFIG_FILE) as f:
        return json.load(f)


def save_config(data):

    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)
