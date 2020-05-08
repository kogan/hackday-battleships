import os

import requests
from flask import Flask, jsonify, request

from engine import attack, setup, wait


def create_app():
    app = Flask(__name__)

    @app.route("/", methods=["POST"])
    def start_game():
        try:
            data = request.json
            token = os.environ.get("GAME_TOKEN")
            url = data["url"]
            game_id = data["game_id"]
            session = requests.Session()
            session.headers.update(dict(Authorization=f"Token {token}"))
            print(f"Starting game: {game_id=} {url}")
            ships, config = setup(session, url, game_id)
            print(f"Setup done: {game_id=} {ships} {config} {url}")
            wait(session, url, game_id, "attack")
            print(f"Beginning attack: {game_id=}")
            attack(session, url, game_id, config)
            print(f"Complete: {game_id=}")
            return jsonify(success=True)
        except Exception as ex:
            print("Error: ", str(ex))
            raise

    return app
