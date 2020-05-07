from django.contrib import admin

from .models import BotServer, Game, GameConfig, GameMove, GamePlayer, GameSetup


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


@admin.register(BotServer)
class BotServerAdmin(admin.ModelAdmin):
    pass


@admin.register(GameConfig)
class GameConfigAdmin(admin.ModelAdmin):
    pass
