from django.contrib import admin

from .models import Game, GameMove, GamePlayer, GameSetup


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    pass


@admin.register(GamePlayer)
class GamePlayerAdmin(admin.ModelAdmin):
    pass


@admin.register(GameMove)
class GameMoveAdmin(admin.ModelAdmin):
    pass


@admin.register(GameSetup)
class GameSetupAdmin(admin.ModelAdmin):
    pass
