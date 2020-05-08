from django import forms
from django.conf.urls import url
from django.contrib import admin
from django.contrib.admin import TabularInline
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse

from .models import BotServer, Game, GameConfig, GameException, GameMove, GamePlayer, GameSetup


class PlayerInline(TabularInline):
    model = GamePlayer
    extra = 0


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("created_at", "id", "state", "loser_display", "winner_display")
    readonly_fields = ("loser_display", "winner_display", "created_at")
    inlines = [PlayerInline]
    ordering = ('-created_at',)

    def loser_display(self, obj: Game):
        try:
            return obj.loser
        except GameException:
            return "-"

    def winner_display(self, obj: Game):
        try:
            return obj.winner
        except GameException:
            return "-"

    loser_display.short_description = "Loser"  # type: ignore
    winner_display.short_description = "Winner"  # type: ignore


@admin.register(GamePlayer)
class GamePlayerAdmin(admin.ModelAdmin):
    list_display = ["game", "player", "state"]
    list_filter = ["game", "player", "state"]


@admin.register(GameMove)
class GameMoveAdmin(admin.ModelAdmin):
    list_display = ["id", "player", "x", "y"]
    list_filter = ["player__game"]


@admin.register(GameSetup)
class GameSetupAdmin(admin.ModelAdmin):
    list_display = ["id", "player", "x", "y", "length", "orientation"]
    list_filter = ["player"]


@admin.register(BotServer)
class BotServerAdmin(admin.ModelAdmin):
    list_display = ["user", "server_address"]


@admin.register(GameConfig)
class GameConfigAdmin(admin.ModelAdmin):
    list_display = ["id", "board_size", "player_1", "player_2", "count", "ship_config"]
    list_filter = ["player_1", "player_2"]

    def start_game(self, request, pk):
        config = get_object_or_404(GameConfig, pk=pk)
        game = config.create_game(request.build_absolute_uri("/"),)
        return HttpResponseRedirect(reverse("admin:cloudships_game_change", args=(game.pk,)))

    def start_all_games(self, request, pk):
        config = get_object_or_404(GameConfig, pk=pk)
        config.create_all_games(request.build_absolute_uri("/"))
        return HttpResponseRedirect(
            reverse("admin:cloudships_gameconfig_change", args=(config.pk,))
        )

    def get_urls(self):

        return [
            url(
                r"^(\d+)/start_game/$",
                self.admin_site.admin_view(self.start_game),
                name="start-game",
            ),
            url(
                r"^(\d+)/start_all_games/$",
                self.admin_site.admin_view(self.start_all_games),
                name="start-game",
            ),
        ] + super().get_urls()
