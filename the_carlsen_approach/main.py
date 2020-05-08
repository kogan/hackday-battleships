import itertools
import json
import operator
import os
import random
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urljoin

import requests

# Copied for your convenience
OrientationVertical = "vertical"
OrientationHorizontal = "horizontal"


@dataclass
class DataShip(object):
    x: int
    y: int
    length: int
    orientation: str


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


class BoardState(object):
    def init(self, session, url, game_id, config):
        self.config = config
        self.session = session
        self.url = url
        self.game_id = game_id
        self.board_size = config["board_size"]
        self.board_state = {}
        for x in range(self.board_size):
            for y in range(self.board_size):
                self.board_state[(x, y)] = None
        self.ships_alive = {x['length']: x['alive'] for x in config["ship_config"]}
        self.history = []

    def make_move(self, x, y):
        response = self.session.post(urljoin(self.url, f"/api/game/{self.game_id}/attack/"), json=dict(x=x, y=y))

        self.set_board_state(response.json(), x, y)

    def set_board_state(self, response, x, y):
        self.board_state[(x, y)] = response["result"]
        self.history.append({'coordinate': (x, y), 'result': response["result"]})
        if response["result"] == "SUNK":
            self.update_sunk_ship(x, y)

    def update_sunk_ship(self, x, y):
        size = 1
        c = 1
        while self.board_state.get((x + c, y)) == "HIT":
            size += 1
            self.board_state[(x + c, y)] = "SUNK"
            c += 1
        else:
            self.board_state[(x + c, y)] = "MISS"

        c = 1
        while self.board_state.get((x - c, y)) == "HIT":
            size += 1
            self.board_state[(x - c, y)] = "SUNK"
            c += 1
        else:
            self.board_state[(x - c, y)] = "MISS"

        c = 1
        while self.board_state.get((x, y + c)) == "HIT":
            size += 1
            self.board_state[(x, y + c)] = "SUNK"
            c += 1
        else:
            self.board_state[(x, y+c)] = "MISS"

        c = 1
        while self.board_state.get((x, y - c)) == "HIT":
            size += 1
            self.board_state[(x, y - c)] = "SUNK"
            c += 1
        else:
            self.board_state[(x, y-c)] = "MISS"

        self.ships_alive[size] = self.ships_alive[size] - 1
        if self.ships_alive[size] == 0:
            self.ships_alive.pop(size)

    def enumerate_ship_placements(self, ship_size):
        coordinates = []  # list of coordinates with duplicates expected
        for x, y in self.board_state:
            up_coordinates = []
            valid_placement = True
            if (y + ship_size) < self.config["board_size"]:
                for step in range(ship_size):
                    coord = (x, y + step)
                    if self.board_state[coord] in ['SUNK', 'MISS']:
                        valid_placement = False
                        break
                    up_coordinates.append(coord)

            if valid_placement:
                coordinates.extend(up_coordinates)

            right_coordinates = []
            valid_placement = True
            if (x + ship_size) < self.board_size:
                for step in range(ship_size):
                    coord = (x + step, y)
                    if self.board_state[coord] in ['SUNK', 'MISS']:
                        valid_placement = False
                        break
                    right_coordinates.append(coord)

            if valid_placement:
                coordinates.extend(right_coordinates)

        return coordinates

    def enumerate_all_placements(self):
        all_coordinates = []
        for length, count in self.ships_alive.items():
            ship_coordinates = self.enumerate_ship_placements(length)
            for _ in range(count):
                all_coordinates += ship_coordinates
        return all_coordinates

    def next_move(self):
        all_placements = self.enumerate_all_placements()
        last_move = self.history[-1]
        if last_move.result == "HIT":
            x = last_move.coord[0]
            y = last_move.coord[0]
            candidates = []
            candidates.append((x, y + 1))
            candidates.append((x + 1, y))
            candidates.append((x, y - 1))
            candidates.append((x - 1, y - 1))
            all_placements = filter(lambda coord: coord in candidates, all_placements)
        return Counter(all_placements).most_common(1)[0]


def phase_attack(session, url, game_id, config):
    """
    Attack a random coordinate that hasn't been attacked before.
    """
    bs = BoardState(session, url, game_id, config)


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
