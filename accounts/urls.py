from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

class RPGLoginView(LoginView):
    template_name = "registration/login.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.session["show_dashboard_landing"] = True
        return response

app_name = "accounts"
urlpatterns = [
    path("entrar/", RPGLoginView.as_view(), name="login"),
    path("sair/", LogoutView.as_view(), name="logout"),
]
