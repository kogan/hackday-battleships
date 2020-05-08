import typing as t

import requests
from django.conf import settings

if t.TYPE_CHECKING:
    from .models import BotServer, Game


def dispatch(callback, game: "Game", server_1: "BotServer", server_2: "BotServer"):
    if settings.DEBUG:
        # HACK - internal ports require internal thinking
        callback = "http://django"
    response = requests.post(
        settings.DISPATCH_URL,
        json={
            "players": [
                {"server_url": server_1.server_address, "username": server_1.user.username},
                {"server_url": server_2.server_address, "username": server_2.user.username},
            ],
            "game_id": str(game.pk),
            "callback_url": callback,
        },
    )
    response.raise_for_status()
