from typing import Any

from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404

from accounts.models import User

from .models import Campaign


class RoleRequiredMixin(LoginRequiredMixin, AccessMixin):
    required_role: str = ""

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        if request.user.role != self.required_role:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class MasterRequiredMixin(RoleRequiredMixin):
    required_role = User.Role.MASTER


class PlayerRequiredMixin(RoleRequiredMixin):
    required_role = User.Role.PLAYER


class CampaignMemberRequiredMixin(LoginRequiredMixin, AccessMixin):
    campaign_url_kwarg = "slug"

    def get_campaign(self) -> Campaign:
        campaign = getattr(self, "campaign", None)
        if campaign is not None:
            return campaign
        slug = self.kwargs.get(self.campaign_url_kwarg)
        if slug is None:
            obj = self.get_object()
            campaign = obj if isinstance(obj, Campaign) else getattr(obj, "campaign", None)
        else:
            campaign = get_object_or_404(Campaign, slug=slug)
        if campaign is None:
            raise ImproperlyConfigured("A view deve fornecer uma campanha.")
        self.campaign = campaign
        return campaign

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not self.get_campaign().has_member(request.user):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class CharacterOwnerRequiredMixin(LoginRequiredMixin, AccessMixin):
    """Protect an object exposing a ``user_id`` owner (used from Phase 2)."""

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        character = self.get_object()
        campaign = getattr(character, "campaign", None)
        is_campaign_master = campaign and campaign.master_id == request.user.pk
        if character.user_id != request.user.pk and not is_campaign_master:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
