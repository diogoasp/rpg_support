from django.urls import path

from .views import RPGLoginView, RequiredPasswordChangeView, LogoutView

app_name = "accounts"
urlpatterns = [
    path("entrar/", RPGLoginView.as_view(), name="login"),
    path("trocar-senha-obrigatoria/", RequiredPasswordChangeView.as_view(), name="force_password_change"),
    path("sair/", LogoutView.as_view(), name="logout"),
]
