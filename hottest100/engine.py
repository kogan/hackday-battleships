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


class Tile:
    position: Point
    state: State


@dataclass
class DataShip:
    position: Point
    length: int
    orientation: Orientation


@dataclass
class Board:
    tiles: t.List[t.List[Tile]]


@dataclass
class Engine:

    def generate_board(self):
        return Board()

    def get_attack(self) -> Point:
        return Point(0, 0)

    def test(self):
        self.board = self.generate_board()
