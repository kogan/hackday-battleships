from cloudships.models import Game, GameException, GamePlayer, Orientation
from django.http import JsonResponse
from rest_framework import serializers
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated


class ShipSerializer(serializers.Serializer):
    length = serializers.IntegerField(required=True)
    count = serializers.IntegerField(required=True)


class CreateGameSerializer(serializers.Serializer):
    board_size = serializers.IntegerField(default=10, required=False)
    ship_config = ShipSerializer(many=True, required=True)


class ShipSerializer(serializers.Serializer):
    x = serializers.IntegerField(required=True)
    y = serializers.IntegerField(required=True)
    length = serializers.IntegerField(required=True)
    orientation = serializers.ChoiceField(Orientation.choices, required=True)


class AttackSerializer(serializers.Serializer):
    x = serializers.IntegerField(required=True)
    y = serializers.IntegerField(required=True)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_game(request):
    form = CreateGameSerializer(data=request.data)
    if not form.is_valid():
        return JsonResponse(dict(errors=form.errors), status=400)
    game = Game.objects.create(**form.validated_data)
    return JsonResponse(dict(game_id=game.id))


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def join_game(game_id, request):
    try:
        Game.objects.join_game(game_id, request.user)
        return JsonResponse(dict(game_id=game_id))
    except GameException as e:
        return JsonResponse(dict(errors=[str(e)]), status=400)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def place_ships(game_id, request):
    form = ShipSerializer(data=request.data, many=True)
    if not form.is_valid():
        return JsonResponse(dict(errors=form.errors), status=400)
    try:
        GamePlayer.objects.add_ships(game_id, request.user, form.validated_data)
    except GameException as e:
        return JsonResponse(dict(errors=[str(e)]), status=400)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def attack(game_id, request):
    form = AttackSerializer(data=request.data)
    if not form.is_valid():
        return JsonResponse(dict(errors=form.errors), status=400)
    try:
        result = GamePlayer.objects.make_move(
            game_id, request.user, form.validated_data["x"], form.validated_data["y"]
        )
        return JsonResponse(dict(result=result.value, **form.validated_data))
    except GameException as e:
        return JsonResponse(dict(errors=[str(e)]), status=400)
