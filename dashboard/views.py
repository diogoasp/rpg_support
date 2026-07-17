from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from campaigns.mixins import MasterRequiredMixin, PlayerRequiredMixin
from campaigns.models import Campaign


class DashboardRedirectView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_master:
            return redirect("dashboard:master")
        return redirect("dashboard:player")


class MasterDashboardView(MasterRequiredMixin, TemplateView):
    template_name = "dashboard/master.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["campaigns"] = Campaign.objects.filter(
            master=self.request.user
        ).prefetch_related("players")
        return context


class PlayerDashboardView(PlayerRequiredMixin, TemplateView):
    template_name = "dashboard/player.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["campaigns"] = self.request.user.campaigns.select_related("master")
        return context
