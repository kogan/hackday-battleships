import enum
import random
import typing as t
from dataclasses import asdict, dataclass

# hard coded for now
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
    ships: t.List[Ship]
    width: int
    height: int

    def blank(self):
        # dimension out a blank board of width x height
        for x in range(self.height):
            row = []
            for y in range(self.width):
                row.append(Tile(position=Point(x,y), state=State.Empty))
            self.tiles.append(row)

    def populate_board(self):
        # flesh out a board with ships placed per some strategy
        pass


@dataclass
class Engine:
    our_board: Board
    opponent_board: Board
    test_board: Board
    size: int = 10

    def generate_board(self) -> Board:
        self.our_board = Board(tiles=[], ships=[])
        return self.our_board

    def get_attack(self) -> Point:
        [x, y] = random.sample(range(self.size), 2)
        return Point(x, y)

    def test(self):
        self.our_board = self.generate_board()
        self.test_board = self.generate_board()
