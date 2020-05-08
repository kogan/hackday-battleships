import itertools
import json
import operator
import os
import random
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass
from urllib.parse import urljoin

import requests
import logging

log = logging.getLogger(__name__)

from flask import Flask, request, jsonify

app = Flask(__name__)

# Copied for your convenience
OrientationVertical = "vertical"
OrientationHorizontal = "horizontal"

print("running carlsen approach")


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
        self.board = [["   "] * config["board_size"] for _ in range(config["board_size"])]
        self.board_size = config["board_size"]
        self.board_state = {}
        for x in range(self.board_size):
            for y in range(self.board_size):
                self.board_state[(x, y)] = None
        self.ships_alive = {x['length']: x['count'] for x in config["ship_config"]}
        self.history = []
        self.hit_mode = None

    def make_move(self, coord):
        x, y = coord
        response = self.session.post(urljoin(self.url, f"/api/game/{self.game_id}/attack/"), json=dict(x=x, y=y))
        self.set_board_state(response.json(), x, y)
        return len(self.ships_alive.keys()) > 0

    def set_board_state(self, response, x, y):
        self.board_state[(x, y)] = response["result"]
        if response["result"] == "MISS":
            self.board[x][y] = " o "
        else:
            self.board[x][y] = " X "

        self.history.append({'coordinate': (x, y), 'result': response["result"]})
        if response["result"] == "SUNK":
            self.board[x][y] = " S "
            self.update_sunk_ship(x, y)

        print_2d_array(self.board)

    def in_bounds(self, coord):
        x, y = coord
        return x >= 0 and x < self.board_size and y >= 0 and y < self.board_size

    def surrounding_coords(self, coord):
        x, y = coord
        return filter(self.in_bounds, [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)])

    def update_sunk_ship(self, x, y):
        self.hit_mode = None
        size = 1
        c = 1
        while self.board_state.get((x + c, y)) == "HIT":
            size += 1
            self.board_state[(x + c, y)] = "SUNK"
            self.board[x + c][y] = " S "
            c += 1

        c = 1
        while self.board_state.get((x - c, y)) == "HIT":
            size += 1
            self.board_state[(x - c, y)] = "SUNK"
            self.board[x - c][y] = " S "
            c += 1

        c = 1
        while self.board_state.get((x, y + c)) == "HIT":
            size += 1
            self.board_state[(x, y + c)] = "SUNK"
            self.board[x][y + c ] = " S "
            c += 1

        c = 1
        while self.board_state.get((x, y - c)) == "HIT":
            size += 1
            self.board_state[(x, y - c)] = "SUNK"
            self.board[x][y - c ] = " S "
            c += 1



        for coord in self.board_state:
            is_sunk_in_surrrounding = any([self.board_state[x] == "SUNK" for x in self.surrounding_coords(coord)])
            if self.board_state[coord] not in ["SUNK", "HIT"] and is_sunk_in_surrrounding:
                self.board_state[coord] = "MISS"
                self.board[coord[0]][coord[1]] = ' o '


        self.ships_alive[size] = self.ships_alive[size] - 1
        print(f"sunk_ship_size={size}")
        if self.ships_alive[size] == 0:
            self.ships_alive.pop(size)

        print(f"ships_alive={self.ships_alive}")

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
                    if self.board_state[coord] != "HIT":
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
                    if self.board_state[coord] != "HIT":
                        right_coordinates.append(coord)

            if valid_placement:
                coordinates.extend(right_coordinates)

        return coordinates

    def enumerate_all_placements(self):
        print(f"board_state={self.board_state}")
        all_coordinates = []
        for length, count in self.ships_alive.items():
            ship_coordinates = self.enumerate_ship_placements(length)
            for _ in range(count):
                all_coordinates += ship_coordinates
        return all_coordinates


    def direction(self,moves, first_hit_coord):
        for move in moves:
            if move["coordinate"][0] != first_hit_coord[0] and move["coordinate"][1] != first_hit_coord[1]:
                x_diff = move["coordinate"][0] - first_hit_coord[0]
                if x_diff != 0:
                    return OrientationHorizontal
                return OrientationVertical
        return None

    def opposite_direction(self, direction):
        if direction == OrientationHorizontal:
            return OrientationVertical
        return OrientationHorizontal

    def next_move(self):
        try:
            all_placements = self.enumerate_all_placements()
            print(f"unfiltered_move_count={len(all_placements)}")
            print(f"ships_alive={self.ships_alive}")
            if self.hit_mode or (self.history and self.history[-1]["result"] == "HIT"):
                prev_coord = self.history[-1]["coordinate"]
                if self.hit_mode is None:
                    # activate hit mode
                    self.hit_mode = (prev_coord, len(self.history) - 1)
                    x, y = prev_coord
                    candidates = []
                    candidates.append((x, y + 1))
                    candidates.append((x + 1, y))
                    candidates.append((x, y - 1))
                    candidates.append((x - 1, y))

                else:
                    (first_hit_coord, first_hit_move_index) = self.hit_mode
                    hit_mode_moves = self.history[first_hit_move_index:]
                    hit_mode_moves_hit = [x for x in hit_mode_moves if x["result"] == "HIT"]
                    hit_mode_moves_miss = [x for x in hit_mode_moves if x["result"] == "MISS"]

                    direction = self.direction(hit_mode_moves_hit, first_hit_coord)
                    if direction is None:
                        direction = self.opposite_direction(self.direction(hit_mode_moves_miss, first_hit_coord))

                    print(f"hit_mode_direction={direction}")
                    if direction == OrientationVertical:
                        candidates = []
                        for step in [-1,1]:
                            for move in hit_mode_moves_hit:
                                candidates.append((move["coordinate"][0], move["coordinate"][1]+step))
                    else:
                        candidates = []
                        for step in [-1,1]:
                            for move in hit_mode_moves_hit:
                                candidates.append((move["coordinate"][0]+step, move["coordinate"][1]))
                valid_candidates = [coord for coord in candidates if self.in_bounds(coord) and self.board_state[coord] is None]
                random.shuffle(valid_candidates)
                print(f"valid_candidate_count={len(valid_candidates)}")
                if len(valid_candidates) != 0:
                    return valid_candidates[0]
                self.hit_mode = None

            return Counter(all_placements).most_common(1)[0][0]

        except Exception as e:
            print(f"exception={e}")
            sys.stdout.write("EXCEPTION #############################")
            for k,v in self.board_state.items():
                if v is None:
                    return k

def phase_attack(session, url, game_id, config):
    """
    Attack a random coordinate that hasn't been attacked before.
    """
    bs = BoardState()
    bs.init(session, url, game_id, config)
    next_move = bs.next_move()
    print(f"next_move={next_move}")
    print(f"move_number={len(bs.history)}")
    while bs.make_move(next_move):
        print(f"hit_mode={bs.hit_mode}")
        print(f"next_move={next_move}")
        print(f"move_number={len(bs.history)}")
        next_move = bs.next_move()


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


@app.route('/', methods=['POST'])
def game():
    body = request.json
    log.info('in route')
    play_game(body["url"], os.environ.get("GAME_TOKEN"), body["game_id"])
    return jsonify(success=True)


def run():
    log.info('run')
    app.run(host="0.0.0.0", port=int(sys.argv[1]))


if __name__ == "__main__":
    run()
