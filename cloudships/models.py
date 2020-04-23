import itertools
import typing as t
import uuid
from dataclasses import asdict, dataclass
from enum import Enum

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models, transaction


class GameException(Exception):
    pass


class GameStates(models.TextChoices):
    JOIN_PHASE = "join"
    SETUP_PHASE = "setup"
    ATTACK_PHASE = "attack"
    FINISHED = "finished"


class Orientation(models.IntegerChoices):
    HORIZONTAL = 0
    VERTICAL = 1


class AttackEnum(Enum):
    HIT = "HIT"
    MISS = "MISS"
    SUNK = "SUNK"


@dataclass
class ShipConfig(object):
    length: int
    count: int

    def asdict(self) -> dict:
        return asdict(self)


ShipDict = t.TypedDict("ShipDict", {"x": int, "y": int, "length": int, "orientation": Orientation})


class GameManager(models.Manager):
    def create_game(self, board_size: int, ship_configs: t.Sequence[ShipConfig]):
        if not board_size > 0:
            raise GameException("Board size must be > 0")
        # todo: find a better packing algorithm
        consumed_squares = sum(cfg.count * (cfg.length + 3) for cfg in ship_configs)
        if consumed_squares == 0:
            raise GameException("Must have at least 1 ship")
        if consumed_squares > board_size * board_size:
            raise GameException(f"Not enough empty tiles {consumed_squares}")
        return Game.objects.create(
            board_size=board_size,
            state=Game.States.JOIN_PHASE,
            ship_config=[cfg.asdict() for cfg in ship_configs],
        )

    @transaction.atomic
    def join_game(self, game_id: uuid.UUID, player: User):
        qs = self.get_queryset().filter(pk=game_id, state=Game.States.JOIN_PHASE)
        game = qs.select_for_update().first()
        if game is None:
            raise GameException("Not accepting joins")
        players = list(GamePlayer.objects.filter(game=game).values_list("player_id", flat=True))
        if player.pk in players:
            raise GameException("Already joined this game")
        if len(players) >= 2:
            raise GameException("Game is full")
        game.players.add(GamePlayer.objects.create(game=game, player=player))
        if len(players) == 1:
            game.state = game.States.SETUP_PHASE
            game.save()


class Game(models.Model):
    States = GameStates

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    board_size = models.IntegerField()
    ship_config = JSONField()
    state = models.CharField(max_length=20, choices=States.choices)
    objects = GameManager()

    @property
    def config(self) -> t.List[ShipConfig]:
        return [ShipConfig(**cfg) for cfg in self.ship_config]


class GamePlayerQuerySet(models.QuerySet):
    def find_game(self, game_id: uuid.UUID, player: User):
        return self.filter(game_id=game_id, player=player)

    def in_phase(self, state: GameStates):
        return self.annotate(
            correct_phase=models.ExpressionWrapper(
                models.Q(game__state=state), output_field=models.BooleanField()
            )
        )

    def add_ships(self, game_id: uuid.UUID, player: User, ships: t.Sequence[ShipDict]):
        game_player = (
            self.find_game(game_id, player).in_phase(GameStates.SETUP_PHASE).select_related("game")
        ).first()
        if not game_player:
            raise GameException("Cannot find game")
        if not game_player.correct_phase:
            raise GameException("Game is not in setup phase")

        # validate ship config.
        occupied_squares: t.Set[t.Tuple[int, int]] = set()
        required_ships = {
            cfg.length: dict(expected=cfg.count, count=0) for cfg in game_player.game.config
        }
        ship_objs = [GameSetup(player=game_player, **ship) for ship in ships]
        for i, ship in enumerate(ship_objs):
            required_ships[ship.length]["count"] += 1
            squares = ship.occupied_squares
            # 'cause it's a square we can do cool square arithmetic
            all_points = set(itertools.chain.from_iterable(point for point in squares))
            if min(all_points) < 0 or max(all_points) >= game_player.game.board_size:
                raise GameException(f"Ship[{i}] is out of bounds")
            if occupied_squares.intersection(squares):
                raise GameException(f"Ship[{i}] is overlapping another ship")
            occupied_squares.update(squares.union(ship.surrounding_squares))

        for value in required_ships.values():
            if value["count"] != value["expected"]:
                raise GameException(f"Invalid ship configuration")
        with transaction.atomic():
            GameSetup.objects.filter(player=game_player).delete()
            GameSetup.objects.bulk_create(ship_objs)

    def make_move(self, game_id: uuid.UUID, player: User, x: int, y: int) -> AttackEnum:
        # todo: this doesn't work yet.
        game_player = (
            self.find_game(game_id, player)
            .in_phase(Game.States.ATTACK_PHASE)
            .annotate(
                in_bounds=models.ExpressionWrapper(
                    models.Q(game__board_size__gt=x) & models.Q(game__board_size__gt=y),
                    output_field=models.BooleanField(),
                )
            )
            .prefetch_related(models.Prefetch("moves", to_attr="prefetched_moves"))
        )
        game_player = game_player.first()
        if not game_player:
            raise GameException("Cannot find game")
        if not game_player.correct_phase:
            raise GameException("Game is not in attack phase")
        if x < 0 or y < 0 or not game_player.in_bounds:
            raise GameException("Attack is out of bounds")

        # find out if they've moved previously
        previous_moves = {(move.x, move.y) for move in game_player.prefetched_moves}
        if (x, y) in previous_moves:
            raise GameException("Move has already been made")
        # find out if there was a hit.
        enemy_ships = GameSetup.objects.exclude(player=game_player).filter(
            player__game=game_player.game
        )
        result = AttackEnum.MISS
        for ship in enemy_ships:
            squares = ship.occupied_squares
            if (x, y) in squares:
                result = AttackEnum.HIT
                if previous_moves.union({(x, y)}).issuperset(squares):
                    result = AttackEnum.SUNK
                break
        game_player.moves.add(GameMove.objects.create(player=game_player, x=x, y=y))
        return result


class GamePlayer(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="players")
    player = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    objects = GamePlayerQuerySet.as_manager()


class GameSetupQuerySet(models.QuerySet):
    pass


class GameSetup(models.Model):
    Orientation = Orientation

    player = models.ForeignKey(GamePlayer, on_delete=models.CASCADE)
    x = models.IntegerField()
    y = models.IntegerField()
    length = models.IntegerField()
    orientation = models.IntegerField(choices=Orientation.choices)
    objects = GameSetupQuerySet.as_manager()

    @classmethod
    def get_squares(cls, start_x, start_y, length, orientation):
        if orientation == Orientation.VERTICAL:
            return {(start_x, start_y + xlate) for xlate in range(length)}
        return {(start_x + xlate, start_y) for xlate in range(length)}

    @property
    def occupied_squares(self) -> t.Set[t.Tuple[int, int]]:
        return self.get_squares(self.x, self.y, self.length, self.orientation)

    @property
    def surrounding_squares(self) -> t.Set[t.Tuple[int, int]]:
        if self.orientation == Orientation.VERTICAL:
            return (
                self.get_squares(self.x - 1, self.y - 1, self.length + 1, self.orientation)
                .union(self.get_squares(self.x + 1, self.y - 1, self.length + 1, self.orientation))
                .union({(self.x, self.y - 1), (self.x, self.y + self.length)})
            )
        return (
            self.get_squares(self.x - 1, self.y - 1, self.length + 1, self.orientation)
            .union(self.get_squares(self.x - 1, self.y + 1, self.length + 1, self.orientation))
            .union({(self.x - 1, self.y), (self.x + self.length, self.y)})
        )


class GameMoveQuerySet(models.QuerySet):
    def with_total_moves(self):
        # a move is each turn.
        # if there was a hit immediately prior, then the turn isn't added
        return self


class GameMove(models.Model):
    player = models.ForeignKey(GamePlayer, on_delete=models.CASCADE, related_name="moves")
    x = models.IntegerField()
    y = models.IntegerField()
    objects = GameMoveQuerySet.as_manager()
