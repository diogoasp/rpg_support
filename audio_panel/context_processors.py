from .services import get_favorite_audio_assets, get_recent_audio_assets


def master_audio_panel(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated or not request.user.is_master:
        return {}
    return {
        "audio_panel_favorites": get_favorite_audio_assets(user=request.user, limit=5),
        "audio_panel_recent": get_recent_audio_assets(user=request.user, limit=5),
    }
