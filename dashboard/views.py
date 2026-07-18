from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from campaigns.mixins import MasterRequiredMixin, PlayerRequiredMixin
from campaigns.models import Campaign
from characters.models import Character, CharacterCreation
from django.db.models import Prefetch, Q
from ships.models import Ship
from maps.models import CampaignMap
from history.models import SessionRecord
from encounters.models import Encounter
from combat.models import Combat
from audio_panel.models import AudioAsset


class DashboardRedirectView(LoginRequiredMixin, View):
    def get(self, request):
        if request.session.pop("show_dashboard_landing", False):
            view = MasterDashboardView.as_view() if request.user.is_master else PlayerDashboardView.as_view()
            return view(request)
        if request.user.is_master:
            return redirect("dashboard:master")
        return redirect("dashboard:player")


class MasterDashboardView(MasterRequiredMixin, TemplateView):
    template_name = "dashboard/master.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["campaigns"] = Campaign.objects.filter(master=self.request.user).prefetch_related(
            "players", Prefetch("ships", Ship.objects.filter(is_active=True), to_attr="active_ships"),
            Prefetch("maps", CampaignMap.objects.filter(is_active=True).prefetch_related("visible_to_users")[:5], to_attr="dashboard_maps"),
            Prefetch("session_records", SessionRecord.objects.all(), to_attr="dashboard_sessions"),
            Prefetch("encounters", Encounter.objects.filter(status__in=("draft", "ready")).prefetch_related("participants", "enemy_groups")[:5], to_attr="dashboard_encounters"),
            Prefetch("combats", Combat.objects.filter(status__in=("active", "paused")).prefetch_related("combatants"), to_attr="dashboard_combats"),
            Prefetch("audio_assets", AudioAsset.objects.filter(is_active=True, is_favorite=True).order_by("sort_order", "title")[:5], to_attr="dashboard_audio_favorites"),
        )
        return context


class PlayerDashboardView(PlayerRequiredMixin, TemplateView):
    template_name = "dashboard/player.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        visible_maps = CampaignMap.objects.filter(is_active=True, is_visible_to_players=True).filter(Q(visible_to_users=self.request.user) | Q(visible_to_users__isnull=True)).distinct()
        context["campaigns"] = self.request.user.campaigns.select_related("master").prefetch_related(
            Prefetch("characters", Character.objects.filter(user=self.request.user), to_attr="player_characters"),
            Prefetch("character_creations", CharacterCreation.objects.filter(user=self.request.user, status__in=(CharacterCreation.Status.DRAFT, CharacterCreation.Status.READY, CharacterCreation.Status.REOPENED)), to_attr="player_character_creations"),
            Prefetch("ships", Ship.objects.filter(is_active=True), to_attr="active_ships"),
            Prefetch("maps", visible_maps, to_attr="dashboard_maps"),
            Prefetch("session_records", SessionRecord.objects.filter(is_published=True), to_attr="dashboard_sessions"),
        )
        return context
