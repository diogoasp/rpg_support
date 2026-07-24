from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from .forms import RequiredPasswordChangeForm


class RPGLoginView(LoginView):
    template_name = "registration/login.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.session["show_dashboard_landing"] = True
        return response

    def get_success_url(self):
        if self.request.user.is_authenticated and self.request.user.password_change_required:
            return reverse("accounts:force_password_change")
        return super().get_success_url()


class RequiredPasswordChangeView(LoginRequiredMixin, View):
    template_name = "registration/force_password_change.html"

    def get(self, request):
        if not request.user.password_change_required:
            return redirect("dashboard:home")
        return render(request, self.template_name, {"form": RequiredPasswordChangeForm(request.user)})

    def post(self, request):
        if not request.user.password_change_required:
            return redirect("dashboard:home")
        form = RequiredPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            user.password_change_required = False
            user.save(update_fields=("password_change_required",))
            update_session_auth_hash(request, user)
            messages.success(request, "Senha atualizada. Use a nova senha nos próximos acessos.")
            return redirect("dashboard:home")
        return render(request, self.template_name, {"form": form}, status=422)
