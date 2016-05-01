users = {}


def listen_login(user):
    pass

def add_user(username, passhash):
    pass

    if len(users) == 1:
        listen_login(user)


def send_message(user, room, full_text):



def set_status(user, status):
    if user["status"] != status:
        user["client"].call("UserPresence:setDefaultStatus", [status])


def loop():
    pass


def on_message(*params):
    pass


def on_status_change(*params):
    pass

# def on
