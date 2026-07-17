import mimetypes
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import AudioAssetCreateForm, AudioAssetUpdateForm, AudioFilterForm
from .models import AudioAsset
from .services import (create_audio_asset, deactivate_audio_asset, register_audio_play,
                       toggle_audio_favorite, update_audio_asset)


def _master_assets(request, *, active=None):
    if not request.user.is_authenticated or not request.user.is_master:
        raise Http404
    query = AudioAsset.objects.filter(campaign__master=request.user).select_related("campaign")
    return query.filter(is_active=active) if active is not None else query


@login_required
def library(request):
    query = _master_assets(request)
    form = AudioFilterForm(request.GET)
    if form.is_valid():
        data = form.cleaned_data
        if data["q"]:
            query = query.filter(Q(title__icontains=data["q"]) | Q(tags__icontains=data["q"]))
        for field, lookup in (("category", "category"), ("character", "character_name__icontains"), ("scene", "scene_name__icontains")):
            if data[field]: query = query.filter(**{lookup: data[field]})
        if data["favorite"]: query = query.filter(is_favorite=True)
        if data["active"]: query = query.filter(is_active=data["active"] == "1")
        query = query.order_by({"recent": "-created_at", "used": "-play_count"}.get(data["ordering"], "title"))
    page = Paginator(query, 24).get_page(request.GET.get("page"))
    return render(request, "audio_panel/library.html", {"filter_form": form, "page_obj": page})


@login_required
def edit(request, pk=None):
    obj = get_object_or_404(_master_assets(request), pk=pk) if pk else None
    form_class = AudioAssetUpdateForm if obj else AudioAssetCreateForm
    form = form_class(request.POST or None, request.FILES or None, instance=obj, user=request.user)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        if obj: update_audio_asset(user=request.user, audio_asset=obj, **data)
        else: create_audio_asset(user=request.user, **data)
        return redirect("audio_panel:library")
    return render(request, "audio_panel/form.html", {"form": form, "object": obj})


@login_required
@require_POST
def deactivate(request, pk):
    obj = get_object_or_404(_master_assets(request), pk=pk)
    deactivate_audio_asset(user=request.user, audio_asset=obj)
    return redirect("audio_panel:library")


@login_required
@require_POST
def favorite(request, pk):
    obj = get_object_or_404(_master_assets(request, active=True), pk=pk)
    obj = toggle_audio_favorite(user=request.user, audio_asset=obj)
    return render(request, "audio_panel/partials/favorite_button.html", {"asset": obj})


@login_required
def protected_file(request, pk):
    obj = get_object_or_404(_master_assets(request, active=True), pk=pk)
    field = obj.audio_file
    if not field or not field.name.startswith(f"audio/campaigns/{obj.campaign_id}/"):
        raise Http404
    content_type = mimetypes.guess_type(field.name)[0] or "application/octet-stream"
    if settings.PROTECTED_MEDIA_MODE == "x-accel":
        response = HttpResponse(content_type=content_type)
        response["X-Accel-Redirect"] = settings.PROTECTED_MEDIA_ACCEL_PREFIX.rstrip("/") + "/" + field.name
        response["Content-Disposition"] = f'inline; filename="{Path(field.name).name}"'
        return response
    response = FileResponse(field.open("rb"), content_type=content_type, filename=Path(field.name).name)
    response["Accept-Ranges"] = "bytes"
    response["Cache-Control"] = "private, no-store"
    return response


@login_required
@require_POST
def register_play(request, pk):
    obj = get_object_or_404(_master_assets(request, active=True), pk=pk)
    register_audio_play(user=request.user, audio_asset=obj)
    return JsonResponse({"ok": True}, status=202)
