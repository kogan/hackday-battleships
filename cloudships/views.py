from cloudships.dispatcher import verify_game_secret
from cloudships.models import BotServer, Game, GameConfig, GameException, GamePlayer, Orientation
from django.http import Http404, JsonResponse
from rest_framework import serializers
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView


class ShipConfigSerializer(serializers.Serializer):
    length = serializers.IntegerField(required=True)
    count = serializers.IntegerField(required=True)


class GameDetailSerializer(serializers.Serializer):
    state = serializers.CharField()
    id = serializers.UUIDField()
    loser = serializers.SerializerMethodField(method_name="get_loser")
    is_draw = serializers.SerializerMethodField(method_name="get_is_draw")

    def get_loser(self, game: Game):
        if game.state != Game.States.FINISHED:
            return None
        loser = game.loser
        if loser is None:
            return None
        return loser.player.username

    def get_is_draw(self, game: Game):
        if game.state != Game.States.FINISHED:
            return None
        return game.loser is None


class GameStateSerializer(GameDetailSerializer):
    board_size = serializers.IntegerField(default=10, required=False)
    ship_config = ShipConfigSerializer(many=True, required=True, source="config.ships")
    moves = serializers.SerializerMethodField(method_name="get_move_stream")

    def get_move_stream(self, game: Game):
        if game.state != Game.States.FINISHED:
            return []
        return [
            dict(x=move.x, y=move.y, player=move.player.player.username, result=move.result)
            for move in game.move_stream
        ]


class ShipSerializer(serializers.Serializer):
    x = serializers.IntegerField(required=True)
    y = serializers.IntegerField(required=True)
    length = serializers.IntegerField(required=True)
    orientation = serializers.ChoiceField(Orientation.choices, required=True)


class AttackSerializer(serializers.Serializer):
    x = serializers.IntegerField(required=True)
    y = serializers.IntegerField(required=True)


class FinishedPlayerSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    state = serializers.CharField(required=True)


class FinishGameSerializer(serializers.Serializer):
    players = FinishedPlayerSerializer(many=True)
    secret = serializers.CharField(required=True)


class PlayerSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, source="user.username")


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def players(request):
    players = BotServer.objects.all()
    return JsonResponse(PlayerSerializer(instance=players, many=True).data, safe=False)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def join_game(request, game_id=None):
    try:
        game = GamePlayer.objects.find_game(game_id, request.user).first().game
        return JsonResponse(dict(game=GameStateSerializer(instance=game).data))
    except (GameException, AttributeError) as e:
        return JsonResponse(dict(errors=[str(e)]), status=400)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def game_status(request, game_id=None):
    player = GamePlayer.objects.find_game(game_id, request.user).select_related("game").first()
    if player is None:
        raise Http404
    return JsonResponse(dict(game=GameStateSerializer(instance=player.game).data))


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def place_ships(request, game_id=None):
    form = ShipSerializer(data=request.data, many=True)
    if not form.is_valid():
        return JsonResponse(dict(errors=form.errors), status=400)
    try:
        GamePlayer.objects.add_ships(game_id, request.user, form.validated_data)
        return JsonResponse(dict())
    except GameException as e:
        return JsonResponse(dict(errors=[str(e)]), status=400)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def attack(request, game_id=None):
    form = AttackSerializer(data=request.data)
    if not form.is_valid():
        return JsonResponse(dict(errors=form.errors), status=400)
    try:
        result = GamePlayer.objects.make_move(
            game_id, request.user, form.validated_data["x"], form.validated_data["y"]
        )
        return JsonResponse(dict(result=result, **form.validated_data))
    except GameException as e:
        return JsonResponse(dict(errors=[str(e)]), status=400)


@api_view(["POST"])
def finish_game(request, game_id=None):
    form = FinishGameSerializer(data=request.data)
    if not form.is_valid():
        return JsonResponse(dict(errors=form.errors), status=400)
    if not verify_game_secret(game_id, form.validated_data["secret"]):
        return JsonResponse({}, status=401)
    try:
        Game.objects.finish_game(game_id, form.validated_data["players"])
        return JsonResponse(dict())
    except GameException as e:
        return JsonResponse(dict(errors=[str(e)]), status=400)


class BattleSerializer(serializers.Serializer):
    player_1 = serializers.CharField()
    player_2 = serializers.CharField()


@api_view(["POST"])
def trigger_battle(request):
    form = BattleSerializer(data=request.data)

    if not form.is_valid():
        return JsonResponse(dict(errors=form.errors), status=400)

    p1 = form.validated_data["player_1"]
    p2 = form.validated_data["player_2"]

    gcf = GameConfig.objects.filter(player_1__user__username=p1, player_2__user__username=p2).last()
    # Try the other combo
    if not gcf:
        gcf = GameConfig.objects.filter(player_2__user__username=p1, player_1__user__username=p2).last()
    if not gcf:
        return JsonResponse(dict(errors=["cannot find game config with such players"]), status=400)
    try:
        gcf.create_all_games(request.build_absolute_uri("/"))
        return JsonResponse(dict(), status=200)
    except GameException as e:
        return JsonResponse(dict(errors=[str(e)]), status=400)


class GameConfigSerializer(serializers.Serializer):
    board_size = serializers.IntegerField()
    id = serializers.IntegerField()
    player_1 = serializers.CharField(source="player_1.user.username")
    player_2 = serializers.CharField(source="player_2.user.username")
    count = serializers.CharField(source="game_count")


class GameConfigDetailSerializer(GameConfigSerializer):
    games = GameDetailSerializer(source="game_set", many=True)


class GameConfigListView(APIView):
    def get(self, request, format=None):
        cfgs = GameConfig.objects.all()
        serializer = GameConfigSerializer(cfgs, many=True)
        return JsonResponse(dict(games=serializer.data))


class GameConfigDetailView(APIView):
    def get_object(self, pk):
        try:
            return GameConfig.objects.get(pk=pk)
        except GameConfig.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        cfg = self.get_object(pk)
        serializer = GameConfigDetailSerializer(cfg)
        return JsonResponse(dict(data=serializer.data))
