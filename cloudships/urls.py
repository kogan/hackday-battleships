from django.contrib import admin
from django.urls import path

from .views import (
    GameConfigDetailView,
    GameConfigListView,
    attack,
    finish_game,
    game_status,
    join_game,
    place_ships,
    players,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/game/<uuid:game_id>/", game_status),
    path("api/game/<uuid:game_id>/join/", join_game),
    path("api/game/<uuid:game_id>/place/", place_ships),
    path("api/game/<uuid:game_id>/attack/", attack),
    path("api/game/<uuid:game_id>/finish/", finish_game),
    path("api/games/", GameConfigListView.as_view()),
    path("api/games/<int:pk>/", GameConfigDetailView.as_view()),
    path("api/player/", players),
]
