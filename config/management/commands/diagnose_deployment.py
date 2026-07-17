import os
from pathlib import Path
from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.db import connection

class Command(BaseCommand):
    help = "Diagnostica configuração de deploy sem exibir segredos."
    def handle(self, *args, **options):
        checks = []
        def record(name, ok, detail=""):
            checks.append(ok); self.stdout.write(f"{'OK' if ok else 'FALHA'} {name}{': '+detail if detail else ''}")
        record("DEBUG desativado", not settings.DEBUG)
        record("ALLOWED_HOSTS", bool(settings.ALLOWED_HOSTS), ",".join(settings.ALLOWED_HOSTS))
        try:
            with connection.cursor() as cursor: cursor.execute("SELECT 1")
            record("banco", True)
        except Exception as exc: record("banco", False, exc.__class__.__name__)
        for name in ("STATIC_ROOT", "MEDIA_ROOT", "PROTECTED_MEDIA_ROOT"):
            path = Path(getattr(settings, name)); record(name, path.exists(), str(path))
        record("X-Accel", settings.PROTECTED_MEDIA_MODE in {"django", "x-accel"}, settings.PROTECTED_MEDIA_MODE)
        record("HTTPS esperado", bool(settings.SECURE_SSL_REDIRECT) or settings.DEBUG)
        call_command("showmigrations", plan=True, verbosity=0)
        if not all(checks): raise SystemExit(1)
