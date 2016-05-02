from .rocket import User
from . import config, app, data, rocket

from flask import render_template, session, flash, redirect, url_for, request
from flask_oauthlib.client import OAuth
from hashlib import sha256
import requests
oauth = OAuth()

slack_oauth = oauth.remote_app(
    "slack",
    base_url = "https://slack.com/api/",
    access_token_url = "https://slack.com/api/oauth.access",
    authorize_url = "https://slack.com/oauth/authorize",
    consumer_key = config["slack"]["oauth"]["client_id"],
    consumer_secret = config["slack"]["oauth"]["client_secret"],
    request_token_params = {"scope": "chat:write:user"},
)

@slack_oauth.tokengetter
def slack_tokengetter():
    return session.get("slack_token")

@app.route("/slack_oauth")
def site_slack_oauth():
    return slack_oauth.authorize(
        callback = "https://dev.mita.me/slack_callback"
        )


@app.route("/slack_callback")
def slack_oauth_callback():
    resp = slack_oauth.authorized_response()

    if resp is None or not resp["ok"]:
        flash("Access was denied")
        return redirect("/")

    session["slack_token"] = (resp["access_token"], resp["access_token"])
    user_data = slack_oauth.post("auth.test")

    username = user_data.data["user"]
    session["username"] = username


    uid = data.add_user({
        "username": username,
        "slack_data":{
            "token": resp["access_token"],
            "user_id": resp["user_id"]
        }
    })
    session["uid"] = uid




    return redirect("/settings")


def fix_slack_requests(uri, headers, body):
    if body == "":
        body = "token=%s" % headers.get("Authorization").lstrip("Bearer ")
    else:
        body += "&token=%s" % headers.get("Authorization").lstrip("Bearer ")
    print(uri, headers, body)
    return (uri, headers, body)

slack_oauth.pre_request = fix_slack_requests


@app.route("/")
def site_index():
    return render_template("index.html")


@app.route("/settings", methods=["GET", "POST"])
def site_settings():
    if request.method == "GET":
        if session.get("uid"):
            return render_template("settings.html")
        else:
            return redirect("/slack_oauth")
    else:
        password = request.form["password"]
        password_confirm = request.form["password-confirm"]
        relay_enabled = request.form["relay_enabled"]

        if password != password_confirm:
            return "passwords did not match"


        rocket.bot.set_password(session["username"], password)

        hasher = sha256()
        hasher.update(password.encode("utf8"))
        passhash = hasher.hexdigest()

        data.users[session["username"]]["rocket"] = {
            "passhash": passhash,
            "username": session["username"],
            "enabled": relay_enabled,
        }

        data.save_data()
        return "saved!"
