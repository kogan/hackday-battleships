import enum
import random
import typing as t
from collections import deque
from dataclasses import asdict, dataclass
from pprint import pprint

SHIP_CONFIG = [
    {"count": 1, "length": 5},
    {"count": 1, "length": 4},
    {"count": 2, "length": 3},
    {"count": 1, "length": 2},
]


class Orientation(enum.Enum):
    Vertical = "vertical"
    Horizontal = "horizontal"


class State(enum.Enum):
    Unknown = "?"
    Hit = "X"
    Empty = "O"


class Health(enum.Enum):
    Alive = 0
    Dead = 1


@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def __repr__(self):
        return f"({self.x},{self.y})"

    def next_point(self, orientation: Orientation):
        if orientation is Orientation.Horizontal:
            return Point(self.x + 1, self.y)
        return Point(self.x, self.y + 1)


@dataclass
class Tile:
    position: Point
    state: State

    def __repr__(self):
        return f"{self.position}: {self.state.value}"


@dataclass
class Ship:
    position: Point
    length: int
    orientation: Orientation
    health: Health
    points_remaining: t.Set[Point]

    def __init__(self, position: Point, length: int, orientation: Orientation):
        self.position = position
        self.length = length
        self.orientation = orientation
        self.health = Health.Alive
        self.points_remaining = set()
        self._init_tiles()

    def _init_tiles(self):
        position = self.position
        for _ in range(self.length):
            self.points_remaining.add(position)
            position = position.next_point(self.orientation)

    def hit(self, point: Point) -> bool:
        if point not in self.points_remaining:
            return False
        self.points_remaining.remove(point)
        if not self.points_remaining:
            self.health = Health.Dead
        return True


@dataclass
class Board:
    tiles: t.List[t.List[Tile]]
    size: int = 10

    @classmethod
    def empty(cls, size: int):
        tiles = [
            [Tile(Point(y, x), state=State.Unknown) for x in range(size)]
            for y in range(size)
        ]
        return Board(tiles=tiles, size=size)


class ShipPlacer:

    """
    >>> placer = ShipPlacer()
    >>> placer.random_ships(size=10)
    """

    def random_ships(self, size, ship_config=None) -> t.List[Ship]:
        ships : t.List[Ship] = []
        # place ships randomly on board
        # XXX: this will not detect if there are too many ships to fit on the board and so will run forever
        if ship_config is None:
            ship_config = SHIP_CONFIG

        for ship_type in ship_config:
            count = ship_type["count"]
            length = ship_type["length"]

            for c in range(count):
                is_clash = True
                while is_clash:
                    orientation = random.choice(list(Orientation))
                    if orientation == Orientation.Vertical:
                        x = random.randrange(0, size)
                        y = random.randrange(0, size - length)
                    else:
                        x = random.randrange(0, size - length)
                        y = random.randrange(0, size)

                    # TODO: collision detection
                    new_ship = Ship(
                        position=Point(x, y), length=length, orientation=orientation
                    )
                    is_clash = self.clash(ships, new_ship)
                    # if is_clash:
                    #    print("clash!")

                ships.append(new_ship)
                # print(new_ship)
                # self.ship_repr(size, ships)

        return ships

    def clash(self, ships, new_ship):
        # Detect if current placement clashes with existing ships
        if not ships:
            return False

        # create a bit list of all points that have a ship on them
        excluded_points = []
        for ship in ships:
            ship_exclusion_zone = []
            if ship.orientation == Orientation.Horizontal:
                for j in [-1, 0, 1]:
                    ship_exclusion_zone.extend(
                        [
                            Point(ship.position.x + i, ship.position.y + j)
                            for i in range(-1, ship.length + 1)
                        ]
                    )
            else:
                for i in [-1, 0, 1]:
                    ship_exclusion_zone.extend(
                        [
                            Point(ship.position.x + i, ship.position.y + j)
                            for j in range(-1, ship.length + 1)
                        ]
                    )
            excluded_points.extend(ship_exclusion_zone)

        if new_ship.orientation == Orientation.Horizontal:
            new_ship_points = [
                Point(new_ship.position.x + i, new_ship.position.y)
                for i in range(new_ship.length)
            ]
        else:
            new_ship_points = [
                Point(new_ship.position.x, new_ship.position.y + j)
                for j in range(new_ship.length)
            ]

        # enumerate all existing ship points to see if there's overlap
        for p in new_ship_points:
            if p in excluded_points:
                return True

        return False

    def ship_repr(self, size, ships):
        # dump out board representation for debugging
        board = []
        for y in range(size):
            board.append([" "] * size)

        for ship in ships:
            for i in range(ship.length):
                if ship.orientation == Orientation.Horizontal:
                    board[ship.position.y][ship.position.x + i] = "S"
                else:
                    board[ship.position.y + i][ship.position.x] = "S"

        print("|   | " + " | ".join(map(str, range(size))) + " |")
        for i, row in enumerate(board):
            print("| {} | ".format(i) + " | ".join(row) + " |")


class AttackResponse(enum.Enum):
    Hit = "hit"
    Miss = "miss"
    Sunk = "sunk"
    Win = "win"
    Invalid = "invalid"
    DNF = "dnf"


class Coordinator:
    def attack(self, point: Point) -> AttackResponse:
        return AttackResponse.Win

    def set_placement(self, board: Board) -> bool:
        return True


@dataclass
class Engine:
    opponent_board: Board
    our_board: t.Optional[Board] = None
    size: int = 10

    def __init__(self, size=10):
        self.size = size
        self.opponent_board = Board.empty(size=size)
        self.is_attack_mode_target = False
        self.attack_queue = deque()

    def generate_board(self) -> Board:
        self.our_board = Board(tiles=[])
        return self.our_board

    def _attack_get_random_disparate_point_with_state_unknown(self) -> Point:
        # Try random disparate (i.e. x, y have different parity) point 10 times
        iterations = 0
        while iterations < 10:
            y = random.randint(0, self.size - 1)
            y_parity = y & 1
            x = 2 * random.randint(0, (self.size >> 1) - 1) + (y_parity ^ 1)
            if self.opponent_board.tiles[x][y].state == State.Unknown:
                return Point(x, y)
            iterations += 1
        # Then just walk through disparate points sequentially. This shouldn't
        # need an iteration count guard, but I'm leaving it, just to be sure
        # it won't ever get stuck here.
        iterations = 0
        while iterations < 10:
            x += 2
            if x >= self.size:
                x = y_parity
                y_parity ^= 1
                y = 0 if y == self.size - 1 else y + 1
            if self.opponent_board.tiles[x][y].state == State.Unknown:
                return Point(x, y)
            iterations += 1
        # If all else fails just walk through points one by one.
        iterations = 0
        while iterations < self.size ** 2:
            x += 1
            if x == self.size:
                x = 0
                y = 0 if y == self.size - 1 else y + 1
            if self.opponent_board.tiles[x][y].state == State.Unknown:
                return Point(x, y)
            iterations += 1
        # If all else fails and more, just return a random point regardless of state.
        [x, y] = random.sample(range(self.size), 2)
        return Point(x, y)

    def _attack_get_target_mode_point(self) -> Point:
        while len(self.attack_queue):
            attack = self.attack_queue.popleft()
            if self.opponent_board.tiles[attack.x][attack.y].state == State.Unknown:
                return attack
        # Queue exhausted. Switch off target mode.
        self.is_attack_mode_target = False
        return self._attack_get_random_disparate_point_with_state_unknown()

    def _attack_enqueue_if_unknown(self, point):
        if self.opponent_board.tiles[point.x][point.y].state == State.Unknown:
            self.attack_queue.append(point)

    def _attack_enqueue_adjacent(self, attack):
        if attack.y > 0:
            self._attack_enqueue_if_unknown(Point(attack.x, attack.y - 1))
        if attack.x < self.size - 1:
            self._attack_enqueue_if_unknown(Point(attack.x + 1, attack.y))
        if attack.y < self.size - 1:
            self._attack_enqueue_if_unknown(Point(attack.x, attack.y + 1))
        if attack.x > 0:
            self._attack_enqueue_if_unknown(Point(attack.x - 1, attack.y))
        self.is_attack_mode_target = (len(self.attack_queue) > 0)

    def get_attack(self) -> Point:
        if self.is_attack_mode_target:
            return self._attack_get_target_mode_point()
        else:
            return self._attack_get_random_disparate_point_with_state_unknown()

    def play(self, coordinator: Coordinator):
        response = AttackResponse.Miss
        while response != AttackResponse.Win:
            attack = self.get_attack()
            response = coordinator.attack(attack)
            tile = self.opponent_board.tiles[attack.x][attack.y]
            if response is AttackResponse.Hit:
                tile.state = State.Hit
                self._attack_enqueue_adjacent(attack)
            elif response is AttackResponse.Sunk:
                tile.state = State.Hit
            elif response is AttackResponse.Win:
                tile.state = State.Hit
            elif response is AttackResponse.Miss:
                tile.state = State.Empty
            elif response is AttackResponse.Invalid:
                print(f"Uh Oh: we messed up with {attack}")


class TestCoordinator(Coordinator):
    def __init__(self, engine: Engine, max_moves=10):
        self.engine = engine
        self.game_board = engine.generate_board()
        self.attacks: t.Set[Point] = set()
        self.moves = 0
        self.max_moves = max_moves
        placer = ShipPlacer()
        self.ships = placer.random_ships(size=engine.size)
        attack_map : t.Dict[Point, Ship] = {}
        for ship in self.ships:
            for point in ship.points_remaining:
                attack_map[point] = ship
        self.attack_map = attack_map

    def print_attack(self, point: Point, response: AttackResponse):
        print(f"Attack: {point} | {response} ({len(self.attack_map)} remaining)")

    def attack(self, point: Point) -> AttackResponse:
        if point in self.attacks or point.x >= self.engine.size or point.y >= self.engine.size:
            response = AttackResponse.Invalid
            self.print_attack(point, response)
            return response

        # TODO, moves calculation means we need to inc moves for the first hit,
        # but not for a free hit.

        self.attacks.add(point)
        ship = self.attack_map.pop(point, None)
        if not ship:
            self.moves += 1
            response = AttackResponse.Miss
            self.print_attack(point, response)
            return response

        # Hit!
        ship.hit(point)
        if ship.health is Health.Dead:
            response = AttackResponse.Sunk
        else:
            response = AttackResponse.Hit
        self.print_attack(point, response)
        if not self.attack_map:
            response = AttackResponse.Win
            self.print_attack(point, response)
        return response

    def set_placement(self, board: Board) -> bool:
        return True


if __name__ == "__main__":
    size = 10
    engine = Engine(size=size)
    coordinator = TestCoordinator(engine, max_moves=100)
    engine.play(coordinator)
    print(f"Game finished with {coordinator.moves} moves")
