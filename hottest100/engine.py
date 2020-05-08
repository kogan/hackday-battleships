import enums
import typing as t
from dataclasses import asdict, dataclass


class Orientation(enums.Enum):
    Veritcal = "vertical"
    Horizontal = "horizontal"


class State(enums.Enum):
    Unknown = "unknown"
    Hit = "hit"
    Empty = "empty"


@dataclass
class Point:
    x: int
    y: int


@dataclass
class Tile:
    position: Point
    state: State


@dataclass
class Ship:
    position: Point
    length: int
    orientation: Orientation


@dataclass
class Board:
    tiles: t.List[t.List[Tile]]


@dataclass
class Engine:
    our_board: Board
    opponent_board: Board
    test_board: Board
    size: int = 10

    def generate_board(self) -> Board:
        self.our_board = Board(tiles=[])
        return self.our_board

    def get_attack(self) -> Point:
        return Point(0, 0)

    def test(self):
        self.our_board = self.generate_board()
        self.test_board = self.generate_board()
