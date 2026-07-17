from django.urls import path

from .views import CampaignCreateView, CampaignDetailView, CampaignUpdateView

app_name = "campaigns"
urlpatterns = [
    path("nova/", CampaignCreateView.as_view(), name="create"),
    path("<slug:slug>/", CampaignDetailView.as_view(), name="detail"),
    path("<slug:slug>/editar/", CampaignUpdateView.as_view(), name="update"),
]
