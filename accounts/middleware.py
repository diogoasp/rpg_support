from django.shortcuts import redirect
from django.urls import reverse


class RequiredPasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated and user.password_change_required:
            allowed_paths = {
                reverse("accounts:force_password_change"),
                reverse("accounts:logout"),
            }
            if (
                request.path not in allowed_paths
                and not request.path.startswith("/static/")
                and not request.path.startswith("/media/")
            ):
                return redirect("accounts:force_password_change")
        return self.get_response(request)
