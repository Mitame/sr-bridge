from . import app

import json
from binascii import b2a_hex
from os import urandom

default_config = {
    "rocketchat":{
        "ws_url": "wss://localhost:3000/websocket",
        "username": "bridgebot",
        "passhash": "f806637e43cb9ca47a7004dd3a1d9aa3ef7a06e13c35346638fbe9fa231a5ffd",
    },
    "slack": {
        "oauth": {
            "client_id": "",
            "client_secret": "",
        }
    },
    "site": {
        "port": 5000,
        "secret_key": b2a_hex(urandom(32)).decode("utf8")
    },
}
def merge_dicts(a, b):
    """Use a as base, overwrite with items from b"""
    new_dict = a
    for key, value in b.items():
        if isinstance(value, dict):
            if key in a:
                merge_dicts(a[key], b[key])
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]

    return new_dict


try:
    loaded_config = json.load(open("config.json"))
    config = merge_dicts(default_config, loaded_config)
except IOError:
    print("Config file not found. Loading defaults...")
    print("You should probably edit the config file with your settings.")
    config = default_config

json.dump(
    config,
    open("config.json", "w"),
    sort_keys = True,
    indent = 2,
    separators = (',', ': ')
)

app.secret_key = config["site"]["secret_key"]
