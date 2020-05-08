import enum
import random
import typing as t
from dataclasses import asdict, dataclass


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

    def generate_board(self) -> Board:
        self.our_board = Board(tiles=[])
        return self.our_board

    def get_attack(self) -> Point:
        [x, y] = random.sample(range(self.size), 2)
        return Point(x, y)

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


class TestCoordinator(Coordinator):
    def __init__(self, engine: Engine):
        self.engine = engine

    def attack(self, point: Point) -> AttackResponse:
        response = AttackResponse.Win
        print(f"Attack: {point} | {response}")
        return response

    def set_placement(self, board: Board) -> bool:
        return True


if __name__ == "__main__":
    size = 10
    engine = Engine(size=size)
    coordinator = TestCoordinator(engine)
    engine.play(coordinator)
