from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("conta/", include("accounts.urls")),
    path("campanhas/", include("campaigns.urls")),
    path("", include("dashboard.urls")),
]
