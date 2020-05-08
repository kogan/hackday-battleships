import enum
import random
import typing as t
from dataclasses import asdict, dataclass
from collections import deque


SHIP_CONFIG = [
    {"count": 1, "length": 5},
    {"count": 1, "length": 4},
    {"count": 2, "length": 3},
    {"count": 1, "length": 2}
]


class Orientation(enum.Enum):
    Vertical = "vertical"
    Horizontal = "horizontal"


class State(enum.Enum):
    Unknown = "?"
    Hit = "X"
    Empty = "O"


@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def __repr__(self):
        return f"({self.x},{self.y})"


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


@dataclass
class Board:
    tiles: t.List[t.List[Tile]]
    size: int = 10

    @classmethod
    def empty(cls, size: int):
        tiles = [[Tile(Point(y, x), state=State.Unknown) for x in range(size)] for y in range(size)]
        return Board(tiles=tiles, size=size)

    def random_ships(self, ship_config=None):
        self.ships = []
        # place ships randomly on board
        # XXX: this will not detect if there are too many ships to fit on the board and so will run forever
        if ship_config is None:
            ship_config = SHIP_CONFIG

        for ship_type in ship_config:
            count = ship_type['count']
            length = ship_type['length']

            for c in range(count):
                orientation = random.choice(list(Orientation))
                if orientation == Orientation.Vertical:
                    x = random.randrange(0, self.size)
                    y = random.randrange(0, self.size - length)
                else:
                    x = random.randrange(0, self.size - length)
                    y = random.randrange(0, self.size)

                # TODO: collision detection
                new_ship = Ship(position=Point(x, y), length=length, orientation=orientation)
                self.ships.append(new_ship)

        return self.ships


class AttackResponse(enum.Enum):
    Hit = "hit"
    Miss = "miss"
    Sunk = "sunk"
    Win = "win"
    Invalid = "invalid"


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
        while iterations < self.size**2:
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
        if len(self.attack_queue):
            return self.attack_queue.popleft()
        else:
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

    def test(self):
        self.our_board = self.generate_board()
        self.test_board = self.generate_board()

    def play(self, coordinator: Coordinator):
        response = AttackResponse.Miss
        while response != AttackResponse.Win:
            attack = self.get_attack()
            response = coordinator.attack(self.get_attack())
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
        self.attacks : t.Set[Point] = set()
        self.moves = 0
        self.max_moves = max_moves

    def attack(self, point: Point) -> AttackResponse:
        self.moves += 1
        if point in self.attacks or point.x >= engine.size or point.y >= engine.size:
            response = AttackResponse.Invalid
        else:
            self.attacks.add(point)
            response = AttackResponse.Hit if self.moves < self.max_moves else AttackResponse.Win
        print(f"Attack: {point} | {response}")
        return response

    def set_placement(self, board: Board) -> bool:
        return True


if __name__ == "__main__":
    size = 10
    engine = Engine(size=size)
    coordinator = TestCoordinator(engine, max_moves=100)
    engine.play(coordinator)
    print(f"Game finished with {coordinator.moves} moves")
