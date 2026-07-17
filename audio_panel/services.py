from typing import Any

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from campaigns.models import Campaign
from .models import AudioAsset


def _authorize(user: Any, campaign: Campaign) -> None:
    if not user.is_authenticated or not user.is_master or campaign.master_id != user.pk:
        raise PermissionError("Campanha não autorizada.")


@transaction.atomic
def create_audio_asset(*, user, **data) -> AudioAsset:
    _authorize(user, data["campaign"])
    return AudioAsset.objects.create(**data)


@transaction.atomic
def update_audio_asset(*, user, audio_asset: AudioAsset, **data) -> AudioAsset:
    _authorize(user, audio_asset.campaign)
    for name, value in data.items():
        setattr(audio_asset, name, value)
    audio_asset.save()
    return audio_asset


def deactivate_audio_asset(*, user, audio_asset: AudioAsset) -> AudioAsset:
    _authorize(user, audio_asset.campaign)
    audio_asset.is_active = False
    audio_asset.save(update_fields=("is_active", "updated_at"))
    return audio_asset


def toggle_audio_favorite(*, user, audio_asset: AudioAsset) -> AudioAsset:
    _authorize(user, audio_asset.campaign)
    audio_asset.is_favorite = not audio_asset.is_favorite
    audio_asset.save(update_fields=("is_favorite", "updated_at"))
    return audio_asset


def register_audio_play(*, user, audio_asset: AudioAsset) -> None:
    _authorize(user, audio_asset.campaign)
    AudioAsset.objects.filter(pk=audio_asset.pk, is_active=True).update(
        play_count=F("play_count") + 1, last_played_at=timezone.now())


def get_recent_audio_assets(*, user, campaign=None, limit=5):
    query = AudioAsset.objects.filter(campaign__master=user, is_active=True, last_played_at__isnull=False)
    if campaign:
        query = query.filter(campaign=campaign)
    return query.select_related("campaign").order_by("-last_played_at")[:limit]


def get_favorite_audio_assets(*, user, campaign=None, limit=10):
    query = AudioAsset.objects.filter(campaign__master=user, is_active=True, is_favorite=True)
    if campaign:
        query = query.filter(campaign=campaign)
    return query.select_related("campaign").order_by("sort_order", "title")[:limit]
