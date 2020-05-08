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
    readonly_fields = ("loser_display", "created_at")
    list_display = ("created_at", "state", "config", "loser_display")
    inlines = [PlayerInline]

    def loser_display(self, obj: Game):
        try:
            return obj.loser
        except GameException as e:
            return str(e)


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


class StartGameForm(forms.Form):
    player_1 = forms.ModelChoiceField(BotServer.objects.all())
    player_2 = forms.ModelChoiceField(BotServer.objects.all())


@admin.register(GameConfig)
class GameConfigAdmin(admin.ModelAdmin):
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
