import itertools
import json
import operator
import os
import random
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass
from enum import Enum
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import List, Tuple
from urllib.parse import urljoin

import requests

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
            get_squares(ship.x - 1, ship.y - 1, ship.length + 1, ship.orientation)
            .union(get_squares(ship.x + 1, ship.y - 1, ship.length + 1, ship.orientation))
            .union({(ship.x, ship.y - 1), (ship.x, ship.y + ship.length)})
            .union(get_occupied_squares(ship))
        )
    return (
        get_squares(ship.x - 1, ship.y - 1, ship.length + 1, ship.orientation)
        .union(get_squares(ship.x - 1, ship.y + 1, ship.length + 1, ship.orientation))
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
    board = [["   "] * board_size for _ in range(board_size)]
    for setup in config:
        for x, y in get_occupied_squares(setup):
            board[x][y] = " O "
    print_2d_array(board)
    return [asdict(cfg) for cfg in config]


def print_2d_array(arr):
    sys.stdout.write("\n")
    for i, (x, y) in enumerate((_x, _y) for _x in range(len(arr)) for _y in range(len(arr[_x]))):
        if i % len(arr) == 0:
            sys.stdout.write("\n")
        sys.stdout.write(arr[x][y])
    sys.stdout.write("\n")


def phase_join(session, url, game_id):
    response = session.post(urljoin(url, f"/api/game/{game_id}/join/"))
    response.raise_for_status()
    config = response.json()["game"]
    return config


def phase_place(session, url, game_id, config):
    ships = make_ship_placement(config["board_size"], config["ship_config"])
    session.post(urljoin(url, f"/api/game/{game_id}/place/"), json=ships)


def clear_heatmap(new_size):
    global RUNNING_HEAT_MAP
    global RUNNING_HEAT_MAP_SIZE
    RUNNING_HEAT_MAP_SIZE = new_size
    RUNNING_HEAT_MAP = Counter()


def mark_hit_on_heatmap(x, y):
    RUNNING_HEAT_MAP[(x, y)] += 1


def phase_attack(session, url, game_id, config):
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
            x, y = choose_next_coord_heat(board_state)
            #x, y = hit_hunter(board_state, ship_hit)
        if x == -1:
            break
        response = session.post(urljoin(url, f"/api/game/{game_id}/attack/"), json=dict(x=x, y=y))
        response = response.json()
        turns += 1
        if response["result"] == "MISS":
            board_state[y][x] = CoordinateState.MISS
        else:
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
            board_state[y][x] = CoordinateState.HIT
            mark_hit_on_heatmap(x, y)

            num_hit += 1

            print_attack_board(board_state)

        print("Turn", turns, (x, y), response["result"], "Remaining:", expected_hits - num_hit)

    if num_hit == expected_hits:
        print("!!!!!!!! GOT THEM ALL !!!!!!!!!!!!")
    else:
        print("WTF??? didnt find something")
    print_attack_board(board_state)
    print("Num turns:", turns)
    print("Score:", turns - num_hit)

    print(RUNNING_HEAT_MAP)


def hit_hunter(board_state, start_coords):

    # local coord vars
    tryX = x
    tryY = y

    # first try hitting up
    up_success = True
    down_success = False
    left_success = False
    right_success = False

    #loop till sunk
    while ship_found:
        if up_success:
            # try up
            if board_state[tryY][tryX] == CoordinateState.UNKNOWN:
                response = try_coord(tryY, tryX)
                if response["result"] == "MISS":
                    board_state[tryY][tryX] = CoordinateState.MISS
                    up_success = False
                    down_success = True
                    tryX = x - 1
                    continue
                elif response["result"] == "HIT":
                    board_state[tryY][tryX] = CoordinateState.HIT
                    up_success = True
                    tryX += 1
                    ship_hit += 1
                    num_hit += 1
                    continue
                else:
                    board_state[y][x] = CoordinateState.HIT
                    ship_found = false
                    num_hit += 1
                    ship_hit = 0
                    break
            else:
                up_success = False
                down_success = True
                tryX = x - 1
                continue
        elif down_success:
            # try down
            if board_state[tryY][tryX] == CoordinateState.UNKNOWN:
                response = try_coord(tryY, tryX)
                if response["result"] == "MISS":
                    board_state[tryY][tryX] = CoordinateState.MISS
                    up_success = False
                    down_success = True
                    tryX = x - 1
                    continue
                elif response["result"] == "HIT":
                    board_state[tryY][tryX] = CoordinateState.HIT
                    up_success = True
                    tryX += 1
                    ship_hit += 1
                    num_hit += 1
                    continue
                else:
                    board_state[y][x] = CoordinateState.HIT
                    ship_found = false
                    num_hit += 1
                    ship_hit = 0
                    break
            else:
                up_success = False
                down_success = True
                tryX = x - 1
                continue
        elif left_success:
            # try left
            pass
        elif right_success:
            # try right
            pass


def choose_next_coord_heat(board_state: List[List[CoordinateState]]) -> Tuple[int, int]:
    for coord, _ in RUNNING_HEAT_MAP.most_common(20):
        x, y = coord
        if board_state[y][x] == CoordinateState.UNKNOWN:
            print("From heatmap")
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
    min_x = max(0, boat_max_x - 1)
    min_y = max(0, boat_max_y - 1)

    for cx in range(min_x, max_x):
        for cy in range(min_y, max_y):
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


def wait_for_state(session, url, game_id, state):
    while True:
        response = session.get(urljoin(url, f"/api/game/{game_id}/")).json()
        if response["game"]["state"] == state:
            break
        time.sleep(5)


def play_game(url: str, token: str, game_id: str):
    session = requests.Session()
    session.headers.update(dict(Authorization=f"Token {token}"))
    print("------------joining-----------------")
    config = phase_join(session, url, game_id)
    print("-------waiting for opponent---------")
    wait_for_state(session, url, game_id, "setup")
    print("---------placing ships--------------")
    phase_place(session, url, game_id, config)
    print("-------waiting for opponent---------")
    wait_for_state(session, url, game_id, "attack")
    print("-----------attacking----------------")
    phase_attack(session, url, game_id, config)


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers["Content-Length"])
            body = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except Exception:
            self.send_response(400, "Invalid Request")
            self.end_headers()
            return
        play_game(body["url"], os.environ.get("GAME_TOKEN"), body["game_id"])
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()


def run():
    server_address = ("", int(sys.argv[1]))
    httpd = HTTPServer(server_address, Handler)
    httpd.serve_forever()


if __name__ == "__main__":
    run()

    # ship_config = [{"count": 1, "length": 5}, {"count": 1, "length": 4}, {"count": 2, "length": 3},
    #                {"count": 1, "length": 2}]
    # board_size = 10
    # for i in range(1_000):
    #     for ship in make_ship_placement(board_size, ship_config):
    #         ship = DataShip(**ship)
    #         for x, y in get_occupied_squares(ship):
    #             mark_hit_on_heatmap(x, y)
    # print(RUNNING_HEAT_MAP)
    #
    # top = dict(RUNNING_HEAT_MAP.most_common(30))
    # max_val = max(top.values())
    # min_val = min(top.values())
    # export_data = Counter()
    # for key, val in top.items():
    #     export_data[key] = int(((val - min_val) / (max_val - min_val)) * 10) + 10
    # print(max_val, min_val, export_data)
