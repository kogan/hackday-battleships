from cloudships.dispatcher import verify_game_secret
from cloudships.models import Game, GameException, GamePlayer, Orientation
from django.http import Http404, JsonResponse
from rest_framework import serializers
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated


class ShipConfigSerializer(serializers.Serializer):
    length = serializers.IntegerField(required=True)
    count = serializers.IntegerField(required=True)


class GameSerializer(serializers.Serializer):
    board_size = serializers.IntegerField(default=10, required=False)
    ship_config = ShipConfigSerializer(many=True, required=True, source="config.ships")


class GameStateSerializer(GameSerializer):
    state = serializers.CharField()
    id = serializers.UUIDField()
    moves = serializers.SerializerMethodField(method_name="get_move_stream")
    loser = serializers.SerializerMethodField(method_name="get_loser")
    is_draw = serializers.SerializerMethodField(method_name="get_is_draw")

    def get_move_stream(self, game: Game):
        if game.state != Game.States.FINISHED:
            return []
        return [
            dict(x=move.x, y=move.y, player=move.player.player.username, result=move.result)
            for move in game.move_stream
        ]

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


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_game(request):
    form = GameSerializer(data=request.data)
    if not form.is_valid():
        return JsonResponse(dict(errors=form.errors), status=400)
    game = Game.objects.create(**form.validated_data)
    return JsonResponse(dict(game_id=game.id))


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
        return JsonResponse(dict(), status=200)
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
