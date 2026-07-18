from typing import Any
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from .models import Character, CharacterCondition

def ensure_master(user: Any, character: Character)->None:
    if not user.is_authenticated or not user.is_master or character.campaign.master_id != user.pk: raise PermissionDenied
def sync_active_combatants(character: Character)->None:
    from combat.models import Combatant
    Combatant.objects.filter(character=character,combat__status__in=('active','paused')).update(current_hp=character.current_hp)
@transaction.atomic
def update_character_resources(*,actor:Any,character:Character,hp:int|None=None,power_points:int|None=None)->Character:
    ensure_master(actor,character); locked=Character.objects.select_for_update().get(pk=character.pk)
    if hp is not None:
        if not 0<=hp<=locked.max_hp: raise ValidationError('PV fora dos limites.')
        locked.current_hp=hp
    if power_points is not None:
        if not 0<=power_points<=locked.max_power_points: raise ValidationError('PP fora dos limites.')
        locked.current_power_points=power_points
    locked.full_clean(); locked.save(); sync_active_combatants(locked); return locked
@transaction.atomic
def damage_character(*,actor:Any,character:Character,amount:int)->Character:
    ensure_master(actor,character)
    if amount < 0: raise ValidationError('O dano não pode ser negativo.')
    locked=Character.objects.select_for_update().get(pk=character.pk)
    locked.current_hp=max(0,locked.current_hp-amount)
    locked.full_clean(); locked.save(update_fields=('current_hp','updated_at')); sync_active_combatants(locked); return locked
@transaction.atomic
def heal_character(*,actor:Any,character:Character,amount:int)->Character:
    ensure_master(actor,character)
    if amount < 0: raise ValidationError('A cura não pode ser negativa.')
    locked=Character.objects.select_for_update().get(pk=character.pk)
    locked.current_hp=min(locked.max_hp,locked.current_hp+amount)
    locked.full_clean(); locked.save(update_fields=('current_hp','updated_at')); sync_active_combatants(locked); return locked
@transaction.atomic
def add_character_condition(*,actor:Any,character:Character,**data)->CharacterCondition:
    ensure_master(actor,character); return CharacterCondition.objects.create(character=character,**data)
@transaction.atomic
def deactivate_character_condition(*,actor:Any,condition:CharacterCondition)->CharacterCondition:
    ensure_master(actor,condition.character); condition.is_active=False; condition.save(update_fields=('is_active','updated_at')); return condition
