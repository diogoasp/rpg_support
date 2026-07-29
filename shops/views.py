from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView

from campaigns.mixins import MasterRequiredMixin, PlayerRequiredMixin
from characters.models import Character

from .models import Shop, ShopAccess, ShopItem
from .services import purchase


class ShopListView(PlayerRequiredMixin, TemplateView):
    template_name = "shops/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["characters"] = Character.objects.filter(user=self.request.user).prefetch_related("shop_accesses__shop__items")
        return context


class PurchaseView(PlayerRequiredMixin, View):
    def post(self, request, pk):
        item = get_object_or_404(ShopItem.objects.select_related("shop"), pk=pk)
        try:
            purchase(actor=request.user, item_id=item.pk)
        except ValidationError as error:
            messages.error(request, error.messages[0])
        else:
            messages.success(request, f"{item.name} foi adicionado ao seu inventário.")
        return redirect("shops:list")


class ToggleAccessView(MasterRequiredMixin, View):
    def post(self, request, shop_pk, character_pk):
        shop = get_object_or_404(Shop, pk=shop_pk, campaign__master=request.user)
        character = get_object_or_404(Character, pk=character_pk, campaign=shop.campaign)
        access, created = ShopAccess.objects.get_or_create(shop=shop, character=character)
        if not created:
            access.delete()
        messages.success(request, f"Acesso de {character.name} à loja {shop.name} atualizado.")
        return redirect("dashboard:master")
