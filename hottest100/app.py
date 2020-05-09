import os

import httpx
from fastapi import FastAPI, Body

from engine import HttpCoordinator


app = FastAPI()


@app.post("/")
async def start_game(url: str = Body(...), game_id: str = Body(...)):
    print("start game request")
    token = os.environ.get("GAME_TOKEN")
    headers = dict(Authorization=f"Token {token}")
    async with httpx.AsyncClient(headers=headers) as client:
        coordinator = HttpCoordinator(client, url, game_id)
        await coordinator.run()
    return {}
