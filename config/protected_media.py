import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpResponse


def protected_file_response(field, *, attachment=False):
    """Return an authorized field through Nginx or Django's safe dev fallback."""
    name = field.name.lstrip("/")
    content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
    disposition = "attachment" if attachment else "inline"
    if settings.PROTECTED_MEDIA_MODE == "x-accel":
        response = HttpResponse(content_type=content_type)
        response["X-Accel-Redirect"] = settings.PROTECTED_MEDIA_ACCEL_PREFIX.rstrip("/") + "/" + name
        response["Content-Disposition"] = f'{disposition}; filename="{Path(name).name}"'
        return response
    response = FileResponse(field.open("rb"), content_type=content_type, as_attachment=attachment, filename=Path(name).name)
    response["Accept-Ranges"] = "bytes"
    response["Cache-Control"] = "private, no-store"
    return response
