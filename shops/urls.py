from django.urls import path

from . import views

app_name = "shops"
urlpatterns = [
    path("lojas/", views.ShopListView.as_view(), name="list"),
    path("lojas/itens/<int:pk>/comprar/", views.PurchaseView.as_view(), name="purchase"),
    path("mestre/lojas/<int:shop_pk>/personagens/<int:character_pk>/acesso/", views.ToggleAccessView.as_view(), name="toggle_access"),
]
