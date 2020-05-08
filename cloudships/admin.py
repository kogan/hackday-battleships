from django.conf.urls import url
from django.contrib import admin
from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse

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


class StartGameForm(forms.Form):
    player_1 = forms.ModelChoiceField(BotServer.objects.all())
    player_2 = forms.ModelChoiceField(BotServer.objects.all())


@admin.register(GameConfig)
class GameConfigAdmin(admin.ModelAdmin):
    def start_game(self, request, pk):
        config = get_object_or_404(GameConfig, pk=pk)
        if request.method == 'POST':
            form = StartGameForm(data=request.POST)
            if form.is_valid():
                game = GameConfig.objects.start_game(
                    config_id=config.id,
                    server_1=form.cleaned_data["player_1"],
                    server_2=form.cleaned_data["player_2"],
                )
                return HttpResponseRedirect(reverse("admin:cloudships_game_change", args=(game.pk,)))
        else:
            form = StartGameForm()
        return TemplateResponse(request, "admin/start_game.html", {"form": form})

    def get_urls(self):
        return [
           url(
               r"^(\d+)/start_game/$",
               self.admin_site.admin_view(self.start_game),
               name="start-game",
           ),
        ] + super().get_urls()
    pass
