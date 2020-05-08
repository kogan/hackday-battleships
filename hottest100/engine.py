import enum
import random
import typing as t
from dataclasses import asdict, dataclass
from collections import deque


class Orientation(enum.Enum):
    Vertical = "vertical"
    Horizontal = "horizontal"


class State(enum.Enum):
    Unknown = "?"
    Hit = "X"
    Empty = "O"


@dataclass
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

    def get_attack(self) -> Point:
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
            elif response is AttackResponse.Sunk:
                tile.state = State.Hit
            elif response is AttackResponse.Win:
                tile.state = State.Hit
            elif response is AttackResponse.Miss:
                tile.state = State.Empty
            elif response is AttackResponse.Invalid:
                print(f"Uh Oh: we messed up with {attack}")


class TestCoordinator(Coordinator):
    def __init__(self, engine: Engine):
        self.engine = engine
        self.game_board = engine.generate_board()
        self.attacks : t.Set[Point] = set()
        self.moves = 0

    def attack(self, point: Point) -> AttackResponse:
        self.moves += 1
        response = AttackResponse.Hit if self.moves < 10 else AttackResponse.Win
        print(f"Attack: {point} | {response}")
        return response

    def set_placement(self, board: Board) -> bool:
        return True


if __name__ == "__main__":
    size = 10
    engine = Engine(size=size)
    coordinator = TestCoordinator(engine)
    engine.play(coordinator)
