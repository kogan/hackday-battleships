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
        tiles = [
            [Tile(Point(y, x), state=State.Unknown) for x in range(size)]
            for y in range(size)
        ]
        return Board(tiles=tiles, size=size)


@dataclass
class Engine:
    our_board: t.Optional[Board] = None
    opponent_board: t.Optional[Board] = None
    size: int = 10

    def generate_board(self) -> Board:
        self.our_board = Board(tiles=[])
        return self.our_board

    def get_attack(self) -> Point:
        [x, y] = random.sample(range(self.size), 2)
        return Point(x, y)

    def test(self):
        self.our_board = self.generate_board()
        self.test_board = self.generate_board()


class EngineRunner:
    def __init__(self, board_size: int = 10):
        self.engine = Engine(size=board_size)
        self.opponent_board = self.engine.generate_board()

    def test(self):
        pass


if __name__ == "__main__":
    runner = EngineRunner()
    runner.test()
