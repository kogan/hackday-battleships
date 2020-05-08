import os
from flask import Flask, request
import requests

from .engine import setup, attack


app = Flask(__name__)


@app.route("/", methods=["POST"])
def start_game():
    data = request.json
    token = os.environ.get("GAME_TOKEN")
    url = data["url"]
    game_id = data["game_id"]

    session = requests.Session()
    session.headers.update(dict(Authorization=f"Token {token}"))
    ships, config = setup(session, url, game_id)
    attack(session, url, game_id, config)
    return "ok", 200
