from django.urls import path

from .views import DashboardRedirectView, MasterDashboardView, PlayerDashboardView

app_name = "dashboard"
urlpatterns = [
    path("", DashboardRedirectView.as_view(), name="home"),
    path("painel/mestre/", MasterDashboardView.as_view(), name="master"),
    path("painel/jogador/", PlayerDashboardView.as_view(), name="player"),
]
