from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("conta/", include("accounts.urls")),
    path("campanhas/", include("campaigns.urls")),
    path("", include("characters.urls")),
    path("", include("inventory.urls")),
    path("", include("ships.urls")),
    path("", include("maps.urls")),
    path("", include("history.urls")),
    path("", include("enemies.urls")),
    path("", include("encounters.urls")),
    path("", include("combat.urls")),
    path("", include("audio_panel.urls")),
    path("", include("dashboard.urls")),
]
