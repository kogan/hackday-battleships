import itertools
import operator
import os
import random
import time
from collections import Counter
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Dict, List, Tuple
from urllib.parse import urljoin

import aiohttp
from fastapi import FastAPI, Body

# Copied for your convenience
OrientationVertical = "vertical"
OrientationHorizontal = "horizontal"

RUNNING_HEAT_MAP_SIZE = 10
RUNNING_HEAT_MAP = Counter({(4, 0): 20, (5, 0): 19, (3, 0): 18, (6, 0): 17, (5, 5): 16, (2, 0): 16, (5, 3): 15, (2, 7): 14, (3, 5): 14, (4, 5): 14, (4, 3): 13, (5, 2): 13, (5, 1): 13, (4, 2): 13, (2, 5): 13, (5, 4): 12, (3, 7): 12, (4, 4): 12, (2, 2): 12, (4, 1): 11, (5, 7): 11, (3, 2): 11, (5, 6): 11, (1, 5): 11, (1, 7): 11, (2, 3): 10, (3, 3): 10, (3, 6): 10, (6, 1): 10, (2, 6): 10})


@dataclass
class DataShip(object):
    x: int
    y: int
    length: int
    orientation: str


class CoordinateState(Enum):
    UNKNOWN = 0
    MISS = 1
    HIT = 2
    BLOCKED = 3  # Cant possibly contain a ship


def get_squares(start_x, start_y, length, orientation):
    if orientation == OrientationVertical:
        return {(start_x, start_y + xlate) for xlate in range(length)}
    return {(start_x + xlate, start_y) for xlate in range(length)}


def get_occupied_squares(ship):
    return get_squares(ship.x, ship.y, ship.length, ship.orientation)


def get_surrounding_squares(ship):
    if ship.orientation == OrientationVertical:
        return (
            get_squares(ship.x - 1, ship.y - 1, ship.length + 2, ship.orientation)
            .union(get_squares(ship.x + 1, ship.y - 1, ship.length + 2, ship.orientation))
            .union({(ship.x, ship.y - 1), (ship.x, ship.y + ship.length)})
            .union(get_occupied_squares(ship))
        )
    return (
        get_squares(ship.x - 1, ship.y - 1, ship.length + 2, ship.orientation)
        .union(get_squares(ship.x - 1, ship.y + 1, ship.length + 2, ship.orientation))
        .union({(ship.x - 1, ship.y), (ship.x + ship.length, ship.y)})
        .union(get_occupied_squares(ship))
    )


def make_ship_placement(board_size: int, ships):
    """
    Place ships in a valid configuration.
    Attempts to randomly place ships first.
    After 3 attempts, place them in order.
    """

    # construct a list of all the ships we need to create, ordered from biggest to smallest
    ships = list(
        itertools.chain.from_iterable(
            [cfg["length"]] * cfg["count"]
            for cfg in sorted(ships, key=operator.itemgetter("length"), reverse=True)
        )
    )

    def try_place(shuffle=True):
        _config = []
        occupied_squares = set()
        for length in ships:
            ship = None
            orientations = [OrientationHorizontal, OrientationVertical]
            _xs = list(range(board_size))
            _ys = list(range(board_size))
            random.shuffle(orientations)
            if shuffle:
                random.shuffle(_xs)
                random.shuffle(_ys)
            for x, y, o in ((_x, _y, _o) for _x in _xs for _y in _ys for _o in orientations):
                ship = DataShip(x, y, length, o)
                if ship.x + length > board_size or ship.y + length > board_size:
                    continue
                occupied = get_occupied_squares(ship)
                if not occupied_squares.intersection(occupied):
                    break
            if ship is None:
                raise ValueError("Couldn't place ships")
            occupied_squares.update(get_surrounding_squares(ship))
            _config.append(ship)
        return _config

    config = None
    for _ in range(2):
        try:
            config = try_place()
            break
        except ValueError:
            continue
    if config is None:
        config = try_place(shuffle=False)
    board = [["  "] * board_size for _ in range(board_size)]
    for setup in config:
        for x, y in get_occupied_squares(setup):
            board[y][x] = "🚢"
    print_2d_array(board)
    return [asdict(cfg) for cfg in config]


def print_2d_array(arr: List[List[str]]):
    print()
    for row in arr:
        print("".join(row))
    print()


async def phase_join(session, url, game_id):
    url = urljoin(url, f"/api/game/{game_id}/join/")
    async with session.post(url) as resp:
        resp.raise_for_status()
        response = await resp.json()
        config = response["game"]
    return config


async def phase_place(session, url, game_id, config):
    ships = make_ship_placement(config["board_size"], config["ship_config"])
    url = urljoin(url, f"/api/game/{game_id}/place/")
    await session.post(url, json=ships)


def clear_heatmap(new_size):
    global RUNNING_HEAT_MAP
    global RUNNING_HEAT_MAP_SIZE
    RUNNING_HEAT_MAP_SIZE = new_size
    RUNNING_HEAT_MAP = Counter()


def mark_hit_on_heatmap(x, y):
    RUNNING_HEAT_MAP[(x, y)] += 1


async def phase_attack(session, url, game_id, config):
    """
    Attack a random coordinate that hasn't been attacked before.
    """
    board_size = config["board_size"]
    if not RUNNING_HEAT_MAP or RUNNING_HEAT_MAP_SIZE != board_size:
        clear_heatmap(board_size)
    board_state = [[CoordinateState.UNKNOWN for _ in range(board_size)] for _ in range(board_size)]
    expected_hits = sum(cfg["count"] * cfg["length"] for cfg in config["ship_config"])
    num_hit = 0
    turns = 0

    ship_found = False
    ship_hit = None

    while num_hit < expected_hits:
        if not ship_found:
            x, y = choose_next_coord_heat(board_state)
        else:
            x, y = hit_hunter(board_state, ship_hit)
        if x == -1:
            break
        async with session.post(urljoin(url, f"/api/game/{game_id}/attack/"), json=dict(x=x, y=y)) as resp:
            response = await resp.json()
        turns += 1
        if "result" not in response:
            if response["errors"] == ["Game is not in attack phase"]:
                return
            print("INVALID MOVE??", x, y, response)
            continue
        if response["result"] == "MISS":
            board_state[y][x] = CoordinateState.MISS
        else:
            board_state[y][x] = CoordinateState.HIT
            if response["result"] == "SUNK":
                # Out of ship found mode
                ship_found = False
                mark_sunk(board_state, x,  y)
            else:
                mark_hit(board_state, x,  y)
                if not ship_found:
                    # Move to ship found mode
                    ship_found = True
                    ship_hit = (x, y)
            mark_hit_on_heatmap(x, y)

            num_hit += 1

        # print("Turn", turns, (x, y), response["result"], "Remaining:", expected_hits - num_hit)
        # if response["result"] != "MISS":
        #     print_attack_board(board_state)

    if num_hit == expected_hits:
        print("!!!!!!!! GOT THEM ALL !!!!!!!!!!!!")
    else:
        print("WTF??? didnt find something")
    print_attack_board(board_state)
    print("Num turns:", turns)
    print("Score:", turns - num_hit)

    print("---------------")
    print("Current heatmap")
    print_heatmap(RUNNING_HEAT_MAP, RUNNING_HEAT_MAP_SIZE)
    print("")


def hit_hunter(board_state, start_coords):
    # try up
    tryX, tryY = start_coords
    tryY -= 1
    while tryY >= 0:
        if board_state[tryY][tryX] == CoordinateState.UNKNOWN:
            return tryX, tryY
        if board_state[tryY][tryX] in (CoordinateState.BLOCKED, CoordinateState.MISS):
            # Cant go further, turn around
            break
        # was hit, continue
        tryY -= 1

    # try down
    tryX, tryY = start_coords
    tryY += 1
    while tryY <= len(board_state) - 1:
        if board_state[tryY][tryX] == CoordinateState.UNKNOWN:
            return tryX, tryY
        if board_state[tryY][tryX] in (CoordinateState.BLOCKED, CoordinateState.MISS):
            # Cant go further, turn around
            break
        # was hit, continue
        tryY += 1

    # try up
    tryX, tryY = start_coords
    tryX -= 1
    while tryX >= 0:
        if board_state[tryY][tryX] == CoordinateState.UNKNOWN:
            return tryX, tryY
        if board_state[tryY][tryX] in (CoordinateState.BLOCKED, CoordinateState.MISS):
            # Cant go further, turn around
            break
        # was hit, continue
        tryX -= 1

    # try down
    tryX, tryY = start_coords
    tryX += 1
    while tryX <= len(board_state[0]) - 1:
        if board_state[tryY][tryX] == CoordinateState.UNKNOWN:
            return tryX, tryY
        if board_state[tryY][tryX] in (CoordinateState.BLOCKED, CoordinateState.MISS):
            # Cant go further, turn around
            break
        # was hit, continue
        tryX += 1
    print('Boat moved!?')
    return -1, -1


def choose_next_coord_heat(board_state: List[List[CoordinateState]]) -> Tuple[int, int]:
    for coord, _ in RUNNING_HEAT_MAP.most_common(20):
        x, y = coord
        if board_state[y][x] == CoordinateState.UNKNOWN:
            return x, y
    return choose_next_coord_random(board_state)


def choose_next_coord_random(board_state: List[List[CoordinateState]]) -> Tuple[int, int]:
    tries = 0
    while True:
        tries += 1
        x = random.randint(0, len(board_state[0]) - 1)
        y = random.randint(0, len(board_state) - 1)
        if board_state[y][x] == CoordinateState.UNKNOWN:
            return x, y
        if tries > 10:
            print("Warn: More than 10 tries.")
            return choose_next_coord_scan(board_state)


def choose_next_coord_scan(board_state: List[List[CoordinateState]]) -> Tuple[int, int]:
    for y, row in enumerate(board_state):
        for x, state in enumerate(row):
            if state == CoordinateState.UNKNOWN:
                return x, y
    print("Exhausted all coords?!")
    return -1, -1


def mark_hit(board_state: List[List[CoordinateState]], x: int, y: int):
    # When we get a hit, the diagonal locations cannot be occupied
    if x > 1 and y > 1:
        if board_state[y-1][x-1] == CoordinateState.UNKNOWN:
            board_state[y-1][x-1] = CoordinateState.BLOCKED
    if x > 1 and y < len(board_state) - 1:
        if board_state[y+1][x-1] == CoordinateState.UNKNOWN:
            board_state[y+1][x-1] = CoordinateState.BLOCKED
    if x < len(board_state[0]) - 1 and y > 1:
        if board_state[y-1][x+1] == CoordinateState.UNKNOWN:
            board_state[y-1][x+1] = CoordinateState.BLOCKED
    if x < len(board_state[0]) - 1 and y < len(board_state) - 1:
        if board_state[y+1][x+1] == CoordinateState.UNKNOWN:
            board_state[y+1][x+1] = CoordinateState.BLOCKED


def mark_sunk(board_state: List[List[CoordinateState]], x: int, y: int):
    # When we have sunk something, find all the surrounding coords
    boat_min_x = x
    boat_min_y = y
    boat_max_x = x
    boat_max_y = y

    while boat_min_x > 1:
        if board_state[y][boat_min_x - 1] == CoordinateState.HIT:
            boat_min_x -= 1
        else:
            break

    while boat_min_y > 1:
        if board_state[boat_min_y - 1][x] == CoordinateState.HIT:
            boat_min_y -= 1
        else:
            break

    while boat_max_x < len(board_state[0]) - 1:
        if board_state[y][boat_max_x + 1] == CoordinateState.HIT:
            boat_max_x += 1
        else:
            break

    while boat_max_y < len(board_state) - 1:
        if board_state[boat_max_y + 1][x] == CoordinateState.HIT:
            boat_max_y += 1
        else:
            break

    max_x = min(len(board_state[0]) - 1, boat_max_x + 1)
    max_y = min(len(board_state) - 1, boat_max_y + 1)
    min_x = max(0, boat_min_x - 1)
    min_y = max(0, boat_min_y - 1)

    for cx in range(min_x, max_x + 1):
        for cy in range(min_y, max_y + 1):
            if board_state[cy][cx] == CoordinateState.UNKNOWN:
                board_state[cy][cx] = CoordinateState.BLOCKED


def print_attack_board(state: List[List[CoordinateState]]):
    print()

    def to_str(p: CoordinateState):
        if p == CoordinateState.HIT:
            return "💥"
        if p == CoordinateState.MISS:
            return "🌊"
        if p == CoordinateState.BLOCKED:
            return "░░"
        return "  "
    for row in state:
        print("".join(to_str(p) for p in row))

    print("\n")


async def wait_for_state(session, url, game_id, state):
    url = urljoin(url, f"/api/game/{game_id}/")
    while True:
        async with session.get(url) as resp:
            response = await resp.json()
            if response["game"]["state"] == "finished":
                raise Exception("Game state is finished!")
            if response["game"]["state"] == state:
                break
        time.sleep(5)


async def play_game(url: str, token: str, game_id: str):
    headers = dict(Authorization=f"Token {token}")
    async with aiohttp.ClientSession(headers=headers) as session:
        print("------------joining-----------------")
        config = await phase_join(session, url, game_id)
        print("-------waiting for opponent---------")
        await wait_for_state(session, url, game_id, "setup")
        print("---------placing ships--------------")
        await phase_place(session, url, game_id, config)
        print("-------waiting for opponent---------")
        await wait_for_state(session, url, game_id, "attack")
        print("-----------attacking----------------")
        await phase_attack(session, url, game_id, config)


app = FastAPI()


@app.post("/")
async def read_root(url: str = Body(...), game_id: str = Body(...)):
    await play_game(url, os.environ.get("GAME_TOKEN"), game_id)
    return {}


def train(ship_config, board_size):
    for i in range(1_000):
        for ship in make_ship_placement(board_size, ship_config):
            ship = DataShip(**ship)
            for x, y in get_occupied_squares(ship):
                mark_hit_on_heatmap(x, y)

    top = dict(RUNNING_HEAT_MAP.most_common(50))
    max_val = max(top.values())
    min_val = min(top.values())
    export_data = Counter()
    for key, val in top.items():
        export_data[key] = int(((val - min_val) / (max_val - min_val)) * 10) + 10
    print(export_data)

    print("Raw heatmap")
    print_heatmap(RUNNING_HEAT_MAP, board_size)
    print("")
    print("Normalised heatmap")
    print_heatmap(export_data, board_size)
    print(export_data)


def print_heatmap(data: Dict[Tuple[int, int], int], board_size: int):
    max_val = max(data.values())
    min_val = min(data.values())
    vis = [["  " for _ in range(board_size)] for _ in range(board_size)]
    symbolrange = ".░▒▓█"
    for (x, y), val in data.items():
        mapped = int(((val - min_val) / (max_val - min_val)) * (len(symbolrange) - 1))
        vis[y][x] = symbolrange[mapped] * 2
    print("\n".join("".join(x) for x in vis))


if __name__ == "__main__":
    train(
        ship_config=[
            {"count": 1, "length": 5},
            {"count": 1, "length": 4},
            {"count": 2, "length": 3},
            {"count": 1, "length": 2},
        ],
        board_size=10,
    )
