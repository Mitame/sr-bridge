from slackclient._server import Server
from slackclient import SlackClient
import json

class Slack:
    def __init__(self, token, debug=False):
        self.debug = debug
        self.slackRTM = Server(token)
        slack = SlackClient(token)
        # Get user listen
        user_response = slack.api_call("users.list")
        self.users = {
            user['id']: user for user in user_response['members']
        }
        self.callbacks = {
            'message': []
        }
        self.slackRTM.rtm_connect()
        self.slackRTM.websocket.sock.setblocking(1)

    def start(self):
        while 1:
            recvd = self.slackRTM.websocket.recv()
            recvd = json.loads(recvd)
            if self.debug: print recvd
            if recvd['type'] == "message" and 'hidden' not in recvd:
                user = self.users[recvd['user']]
                team = recvd['team'] if 'team' in recvd else False
                args = (
                    user['name'],
                    recvd['channel'],
                    recvd['text'],
                    recvd['ts'],
                    team
                )
                self.run_callbacks('message', args)

    def run_callbacks(self, callback_type, args):
        for callback in self.callbacks[callback_type]:
            callback(*args)

    def add_callback(self, callback_type, function):
        self.callbacks[callback_type].append(function)

if __name__ == "__main__":
    slack = Slack("token found at https://api.slack.com/web#authentication", debug=True)
    def on_message(name, channel, message, ts, team):
        print(
            "@%s: %s" %
            (name, message)
        )
    slack.add_callback('message', on_message)
    slack.start()
