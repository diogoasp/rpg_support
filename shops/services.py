from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from characters.models import Character
from inventory.models import InventoryItem

from .models import ShopAccess, ShopItem


def add_purchase_to_inventory(*, character, item):
    inventory_item = (
        InventoryItem.objects.select_for_update()
        .filter(
            character=character,
            name=item.name,
            description=item.description,
            is_active=True,
        )
        .order_by("pk")
        .first()
    )
    if inventory_item is None:
        return InventoryItem.objects.create(
            character=character,
            name=item.name,
            description=item.description,
            quantity=1,
            is_visible=True,
        )
    inventory_item.quantity = (inventory_item.quantity or 0) + 1
    inventory_item.is_visible = True
    inventory_item.save(update_fields=("quantity", "is_visible", "updated_at"))
    return inventory_item


@transaction.atomic
def purchase(*, actor, item_id):
    item = ShopItem.objects.select_for_update().select_related("shop").get(pk=item_id)
    try:
        character = Character.objects.select_for_update().get(
            user=actor,
            campaign=item.shop.campaign,
            campaign__players=actor,
        )
    except Character.DoesNotExist as error:
        raise PermissionDenied("Você não participa da campanha desta loja.") from error
    if not ShopAccess.objects.filter(shop=item.shop, character=character).exists():
        raise PermissionDenied("Você não tem acesso a esta loja.")
    if item.quantity < 1:
        raise ValidationError("Este item está esgotado.")
    if character.money < item.price:
        raise ValidationError("Bellys insuficientes para esta compra.")

    item.quantity -= 1
    item.save(update_fields=("quantity",))
    character.money -= item.price
    character.save(update_fields=("money", "updated_at"))
    add_purchase_to_inventory(character=character, item=item)
    return item, character
