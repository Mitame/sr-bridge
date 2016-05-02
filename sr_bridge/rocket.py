from DDPClient import DDPClient
import string
import random
import time

from . import config

RC_URL=config["rocketchat"]["ws_url"]
DEBUG=True


users = {}

def make_id(length=20):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

class User:
    def __init__(self, username, passhash):
        self.username = username
        self.passhash = passhash

        self.user_id = None
        self.rooms_by_id = {}
        self.rooms_by_name = {}
        self.sub_ids = {}

        self.client = DDPClient(RC_URL, debug=DEBUG)

        self.connected_handlers = {}
        self.changed_handlers = {
            "stream-room-messages": self.on_stream_room_messages
        }
        self.added_handlers = {
            "rocketchat_subscription": self.on_rocketchat_subscription,
            "stream-room-messages": self.on_stream_room_messages
        }

        self.client.on("connected", self.login)
        self.client.on("changed", self.on_changed)
        self.client.on("added", self.on_added)

        self.sent_messages = []
        self.client.connect()

    def login(self):
        self.client.call(
            "login",
            [{
                "user": {"username": self.username},
                "password": {
                    "digest": self.passhash,
                    "algorithm": "sha-256"
                }
            }],
            callback=self.login_callback
        )

    def login_callback(self, u1, user_data):
        print(user_data)
        self.user_id = user_data["id"]
        self.sub_ids["subscription"] = self.client.subscribe("subscription", [])
        # self.join_room("GENERAL", "c")

    def join_room(self, room_id, room_type):
        self.sub_ids[room_id] = {}
        room = None
        while room is None:
            try:
                room = self.rooms_by_id[room_id]
            except KeyError:
                print(self.rooms_by_id)
                time.sleep(1)

        self.sub_ids[room_id]["room"] = self.client.subscribe("room", [room["type"]+room["name"]], callback=print)
        self.sub_ids[room_id]["stream-room-messages"] = self.client.subscribe("stream-room-messages", [room_id, True])

    def on_stream_room_messages(self, collection, id, fields, *args):
        if "args" not in fields:
            return

        data = fields["args"][0]
        user = data["u"]
        if user["_id"] != self.user_id:
            return

        # print(data)
        if "t" in data and data["t"] == "rm":
            self.on_message_removed(data)
        elif "editedAt" in data:
            self.on_message_edited(data)
        elif data["msg"] != "":
            #ignore messages i sent from this client
            if data["_id"] in self.sent_messages:
                return
            self.on_message(data)
        else:
            print("Got unhandled message.")


    def on_changed(self, collection, id, fields, u1):
        if collection in self.changed_handlers:
            try:
                self.changed_handlers[collection](collection, id, fields, u1)
            except Exception as e:
                print("UNHANDLED EXCEPTION:", e)
        else:
            print("unhandled: ", collection, fields)

    def on_added(self, collection, id, fields):
        if collection in self.added_handlers:
            try:
                self.added_handlers[collection](collection, id, fields)
            except Exception as e:
                print("UNHANDLED EXCEPTION:", e)
        else:
            print("unhandled:", collection, fields)

    def on_rocketchat_subscription(self, collection, id, fields):
        data = fields
        room = {
            "name": data["name"],
            "rid": data["rid"],
            "type": data["t"]
        }
        self.rooms_by_id[room["rid"]] = room
        self.rooms_by_name[room["name"]] = room
        self.join_room(room["rid"], room["type"])
        return

    def on_message_removed(self, data):
        print("My message was deleted!")
        print("The message %s was deleted by %s" % (data["_id"], data["editedBy"]["username"]))

    def on_message_edited(self, data):
        print("My message was edited!")
        print("The message %s was edited by %s and now reads '%s'" % (data["_id"], data["editedBy"]["username"], data["msg"]))

    def on_message(self, data):
        print("I sent a message!")
        print("'%s'" % data["msg"])


    def send_message(self, room_id, msg):
        msg_id = make_id()
        print("attempting to send message with id '%s' and text '%s'" % (msg_id, msg))
        self.sent_messages.append(msg_id)
        self.client.call(
            "sendMessage",
            [{
                "_id": msg_id,
                "rid": room_id,
                "msg": msg
            }]
        )

class BotUser(User):
    def __init__(self, username, passhash):
        User.__init__(self, username, passhash)
        self.added_handlers["users"] = self.on_user_data
        self.changed_handlers["users"] = self.on_user_data
        self.users = {}

    def login_callback(self, *args, **kwargs):
        User.login_callback(self, *args, **kwargs)
        self.client.subscribe("fullUserData", ["", 1000])

    def get_user(self, username):
        # print(self.users)
        if username in self.users:
            return self.users[username]
        else:
            return None

    def on_user_data(self, collection, id, data, *args):
        data["id"] = id
        self.users[data["username"]] = data

    def set_password(self, username, password):
        user_data = self.get_user(username)
        print(user_data)
        if user_data is None:
            return False
        self.client.call(
            "insertOrUpdateUser",
            [{
                "_id": user_data["id"],
                "name": user_data["name"],
                "username": user_data["username"],
                "email": user_data["emails"][0]["address"],
                "verified": True,
                "password": password,
                "requirePasswordChange": False,
                "joinDefaultChannels": True,
                "sendWelcomeEmail": True
            }]
        )

bot = BotUser(config["rocketchat"]["username"], config["rocketchat"]["passhash"])
