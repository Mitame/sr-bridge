import os
import json

DATA_PATH = "data.json"

if not os.path.exists(DATA_PATH):
    users = {}
else:
    users = json.load(open(DATA_PATH, "r"))

for user in users.items():
    pass

def save_data():
    json.dump(users, open(DATA_PATH, "w"))


def add_user(data):
     data["user_id"] = len(users)
     users[data["username"]] = data

     save_data()

     return data["user_id"]
