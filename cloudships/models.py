import itertools
import typing as t
import uuid
from dataclasses import asdict, dataclass
from enum import Enum
from functools import cached_property

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models, transaction

from . import dispatcher


class GameException(Exception):
    pass


class GameStates(models.TextChoices):
    JOIN_PHASE = "join"
    SETUP_PHASE = "setup"
    ATTACK_PHASE = "attack"
    FINISHED = "finished"


class Orientation(models.TextChoices):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class AttackEnum(str, Enum):
    HIT = "HIT"
    MISS = "MISS"
    SUNK = "SUNK"


class PlayerStates(models.TextChoices):
    PLAYING = "playing"
    FINISHED = "finished"
    DNF = "dnf"


@dataclass
class ShipConfig(object):
    length: int
    count: int

    def asdict(self) -> dict:
        return asdict(self)


ShipDict = t.TypedDict("ShipDict", {"x": int, "y": int, "length": int, "orientation": Orientation})


@dataclass
class Move(object):
    x: int
    y: int
    player: "GamePlayer"
    result: AttackEnum


class BotServer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    server_address = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username


class GameConfigManager(models.Manager):
    def create_config(self, board_size: int, ship_configs: t.Sequence[ShipConfig]):
        if not board_size > 0:
            raise GameException("Board size must be > 0")
        # todo: find a better packing algorithm
        consumed_squares = sum(cfg.count * (cfg.length + 3) for cfg in ship_configs)
        if consumed_squares == 0:
            raise GameException("Must have at least 1 ship")
        if consumed_squares > board_size * board_size:
            raise GameException(f"Not enough empty tiles {consumed_squares}")
        return GameConfig.objects.create(
            board_size=board_size, ship_config=[cfg.asdict() for cfg in ship_configs],
        )

    def start_game(self, config_id, server_1: BotServer, server_2: BotServer):
        game = Game.objects.create(state=GameStates.JOIN_PHASE, config_id=config_id)
        dispatcher.dispatch(game, server_1, server_2)
        return game


class GameConfig(models.Model):
    board_size = models.IntegerField()
    ship_config = JSONField()
    objects = GameConfigManager()

    @property
    def ships(self) -> t.List[ShipConfig]:
        return [ShipConfig(**cfg) for cfg in self.ship_config]


class GameManager(models.Manager):
    @transaction.atomic
    def join_game(self, game_id: uuid.UUID, player: User) -> "Game":
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
        return game

    def finish_game(self, game_id, players):
        game = (
            Game.objects.filter(id=game_id)
            .prefetch_related(models.Prefetch("players", to_attr="prefetched_players"))
            .first()
        )
        if game is None:
            raise GameException("Game not found")
        player_map = {player["username"]: player["state"] for player in players}
        with transaction.atomic():
            for player in game.prefetched_players:
                player.state = player_map[player.player.username]
                player.save()
            game.state = GameStates.FINISHED
            game.save()


class Game(models.Model):
    States = GameStates
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    state = models.CharField(max_length=20, choices=States.choices)
    config = models.ForeignKey(GameConfig, on_delete=models.CASCADE)
    objects = GameManager()

    @cached_property
    def move_stream(self) -> t.List[Move]:
        """
        Returns a list of moves (in order) for a game.
        """
        players = list(
            self.players.prefetch_related(
                models.Prefetch(
                    "moves", to_attr="prefetched_moves", queryset=GameMove.objects.order_by("id"),
                ),
                models.Prefetch("ships", to_attr="prefetched_ships"),
            )
        )
        if len(players) != 2:
            raise GameException("Player count is not 2")
        p1, p2 = players
        stream: t.List[Move] = []

        # for easy access to find out if a ship is sunk
        p1_shiplog = {}
        p2_shiplog = {}
        for ship in p1.prefetched_ships:
            s = ship.occupied_squares
            for x, y in s:
                p1_shiplog[(x, y)] = s

        for ship in p2.prefetched_ships:
            s = ship.occupied_squares
            for x, y in s:
                p2_shiplog[(x, y)] = s

        def move_gen(player, enemy_log):
            # generate streaks of moves for a player
            # a player gets another turn if there's a hit.
            streak = []
            for move in player.prefetched_moves:
                p = (move.x, move.y)
                if p not in enemy_log:
                    streak.append(Move(x=p[0], y=p[1], player=player, result=AttackEnum.MISS))
                    yield streak
                    streak = []
                else:
                    squares = enemy_log[p]
                    squares.remove(p)
                    if len(squares) == 0:
                        streak.append(Move(x=p[0], y=p[1], player=player, result=AttackEnum.SUNK))
                    else:
                        streak.append(Move(x=p[0], y=p[1], player=player, result=AttackEnum.HIT))
            yield streak

        for m1, m2 in itertools.zip_longest(
            move_gen(p1, p2_shiplog), move_gen(p2, p1_shiplog), fillvalue=[]
        ):
            # player 1 always goes first, but there's no advantage.
            stream.extend(m1)
            stream.extend(m2)
        return stream

    @cached_property
    def loser(self) -> t.Optional["GamePlayer"]:
        moves = self.move_stream
        # determine a loser by last 2 being same player
        # determine a draw by last 2 being different players
        try:
            l, ll = moves[-2:]
        except ValueError:
            # less than 2 moves in the game???
            return None
        if l.player == ll.player:
            return l.player
        return None


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
            self.find_game(game_id, player)
            .in_phase(GameStates.SETUP_PHASE)
            .prefetch_related(models.Prefetch("ships", to_attr="prefetched_ships"))
        ).first()
        if not game_player:
            raise GameException("Cannot find game")
        if not game_player.correct_phase:
            raise GameException("Game is not in setup phase")
        if len(game_player.prefetched_ships) > 0:
            raise GameException("Already placed ships")

        with transaction.atomic():
            game_player = (
                GamePlayer.objects.filter(pk=game_player.pk)
                .select_related("game", "game__config")
                .select_for_update(skip_locked=True, of=("self",))
                .first()
            )
            if game_player is None:
                raise GameException("Race condition")

            # validate ship config.
            occupied_squares: t.Set[t.Tuple[int, int]] = set()
            required_ships = {
                cfg.length: dict(expected=cfg.count, count=0)
                for cfg in game_player.game.config.ships
            }
            ship_objs = [GameSetup(player=game_player, **ship) for ship in ships]
            for i, ship in enumerate(ship_objs):
                required_ships[ship.length]["count"] += 1
                squares = ship.occupied_squares
                # 'cause it's a square we can do cool square arithmetic
                all_points = set(itertools.chain.from_iterable(point for point in squares))
                if min(all_points) < 0 or max(all_points) >= game_player.game.config.board_size:
                    raise GameException(f"Ship[{i}] is out of bounds")
                if occupied_squares.intersection(squares):
                    raise GameException(f"Ship[{i}] is overlapping another ship")
                occupied_squares.update(squares.union(ship.surrounding_squares))

            for value in required_ships.values():
                if value["count"] != value["expected"]:
                    raise GameException(f"Invalid ship configuration")

            GameSetup.objects.bulk_create(ship_objs)

        # if both players have set up, progress to the next stage
        Game.objects.filter(pk=game_player.game.pk).annotate(
            count=models.Count("players__ships__player_id", distinct=True)
        ).filter(count=2).update(state=GameStates.ATTACK_PHASE)

    def make_move(self, game_id: uuid.UUID, player: User, x: int, y: int) -> AttackEnum:
        game_player = (
            self.find_game(game_id, player)
            .in_phase(Game.States.ATTACK_PHASE)
            .annotate(
                in_bounds=models.ExpressionWrapper(
                    models.Q(game__config__board_size__gt=x)
                    & models.Q(game__config__board_size__gt=y),
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
    state = models.CharField(
        choices=PlayerStates.choices, max_length=16, default=PlayerStates.PLAYING
    )
    objects = GamePlayerQuerySet.as_manager()

    def __str__(self):
        return self.player.username


class GameSetupQuerySet(models.QuerySet):
    pass


class GameSetup(models.Model):
    Orientation = Orientation

    player = models.ForeignKey(GamePlayer, on_delete=models.CASCADE, related_name="ships")
    x = models.IntegerField()
    y = models.IntegerField()
    length = models.IntegerField()
    orientation = models.TextField(max_length=15, choices=Orientation.choices)
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


class GameMove(models.Model):
    player = models.ForeignKey(GamePlayer, on_delete=models.CASCADE, related_name="moves")
    x = models.IntegerField()
    y = models.IntegerField()
