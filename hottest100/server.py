import os
from flask import Flask, request
import requests

from .engine import get_ships, attack


app = Flask(__name__)


@app.route("/", methods=["POST"])
def attack():
    data = request.json
    token = os.environ.get("GAME_TOKEN")
    url = data["url"]
    game_id = data["game_id"]

    session = requests.Session()
    session.headers.update(dict(Authorization=f"Token {token}"))
    join_url
    config = session.post()

    get_ships()

    return "ok", 200

# pass in a session
