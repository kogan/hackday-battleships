import typing as t

import requests
from django.conf import settings
from django.utils.crypto import constant_time_compare, get_random_string, salted_hmac

if t.TYPE_CHECKING:
    from .models import BotServer, Game


def generate_signed_id(game_id):
    salt = get_random_string(length=8)
    hmac = salted_hmac(salt, str(game_id)).hexdigest()
    return f"{salt}${hmac}"


def verify_game_secret(game_id, secret):
    salt, hmac = secret.split("$")
    return constant_time_compare(hmac, salted_hmac(salt, str(game_id)).hexdigest())


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
            "secret": generate_signed_id(game.pk),
        },
    )
    response.raise_for_status()
