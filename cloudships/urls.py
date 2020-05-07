from django.contrib import admin
from django.urls import path

from .views import attack, create_game, game_status, join_game, place_ships

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/game/create/", create_game),
    path("api/game/<uuid:game_id>/", game_status),
    path("api/game/<uuid:game_id>/join/", join_game),
    path("api/game/<uuid:game_id>/place/", place_ships),
    path("api/game/<uuid:game_id>/attack/", attack),
]
