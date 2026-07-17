from pathlib import Path

from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def health(request):
    return JsonResponse({"status": "ok"})


def readiness(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        paths = (settings.STATIC_ROOT, settings.MEDIA_ROOT, settings.PROTECTED_MEDIA_ROOT)
        ready = all(Path(path).exists() and Path(path).is_dir() for path in paths)
    except Exception:
        ready = False
    return JsonResponse({"status": "ready" if ready else "unavailable"}, status=200 if ready else 503)
