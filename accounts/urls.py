from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

app_name = "accounts"
urlpatterns = [
    path("entrar/", LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("sair/", LogoutView.as_view(), name="logout"),
]
