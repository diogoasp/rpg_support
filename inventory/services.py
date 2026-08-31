from typing import Any
from django.core.exceptions import ValidationError
from django.db import transaction
from characters.models import Character
from characters.services import ensure_master, ensure_owner, log_character_change
from .models import InventoryItem
@transaction.atomic
def add_inventory_item(*,actor:Any,character:Character,**data)->InventoryItem:
    ensure_master(actor,character); item=InventoryItem(character=character,**data); item.full_clean(); item.save(); return item
@transaction.atomic
def deactivate_inventory_item(*,actor:Any,item:InventoryItem)->InventoryItem:
    ensure_master(actor,item.character); item.is_active=False; item.save(update_fields=('is_active','updated_at')); return item
@transaction.atomic
def use_inventory_item(*,actor:Any,item:InventoryItem)->InventoryItem:
    ensure_owner(actor,item.character)
    locked=InventoryItem.objects.select_for_update().select_related('character').get(pk=item.pk)
    if not locked.is_active or not locked.is_visible: raise ValidationError('Item indisponível.')
    old_quantity=locked.quantity
    if locked.quantity is not None:
        if locked.quantity <= 0: raise ValidationError('Item sem usos disponíveis.')
        locked.quantity-=1
        locked.save(update_fields=('quantity','updated_at'))
    log_character_change(character=locked.character,user=actor,action='use_item',object_type='inventory_item',object_id=locked.pk,description=f'Item usado: {locked.name}',old_value={'quantity':old_quantity},new_value={'quantity':locked.quantity})
    return locked
