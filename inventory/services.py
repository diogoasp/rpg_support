from typing import Any
from django.db import transaction
from characters.models import Character
from characters.services import ensure_master
from .models import InventoryItem
@transaction.atomic
def add_inventory_item(*,actor:Any,character:Character,**data)->InventoryItem:
    ensure_master(actor,character); item=InventoryItem(character=character,**data); item.full_clean(); item.save(); return item
@transaction.atomic
def deactivate_inventory_item(*,actor:Any,item:InventoryItem)->InventoryItem:
    ensure_master(actor,item.character); item.is_active=False; item.save(update_fields=('is_active','updated_at')); return item
