import os

import requests
from flask import Flask, jsonify, request

from engine import HttpCoordinator


def create_app():
    app = Flask(__name__)

    @app.route("/", methods=["POST"])
    def start_game():
        try:
            print("start game request")
            data = request.json
            token = os.environ.get("GAME_TOKEN")
            url = data["url"]
            game_id = data["game_id"]
            session = requests.Session()
            session.headers.update(dict(Authorization=f"Token {token}"))
            coordinator = HttpCoordinator(session, url, game_id)
            coordinator.run()
            return jsonify(success=True)
        except Exception as ex:
            print("Error: ", str(ex))
            raise

    return app
