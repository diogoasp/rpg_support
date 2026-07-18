from django.core.exceptions import PermissionDenied,ValidationError
from django.db import transaction
from campaigns.models import Campaign
from .models import Ship,NAVIGATION_RESOURCE_LEVELS

def _authorize(user,campaign,ship=None):
    if not user.is_authenticated or not user.is_master: raise PermissionDenied
    if ship and ship.campaign_id!=campaign.pk: raise ValidationError('O navio não pertence à campanha.')
@transaction.atomic
def create_or_update_ship(*,user,campaign:Campaign,ship:Ship|None=None,**data)->Ship:
    _authorize(user,campaign,ship)
    ship=ship or Ship(campaign=campaign)
    for key,value in data.items(): setattr(ship,key,value)
    ship.full_clean(); ship.save(); return ship
@transaction.atomic
def assign_ship_to_crew(*,user,campaign:Campaign,ship:Ship)->Ship:
    _authorize(user,campaign,ship)
    if not ship.is_active: raise ValidationError('Somente navios ativos podem pertencer à tripulação.')
    Ship.objects.select_for_update().filter(campaign=campaign,belongs_to_crew=True).exclude(pk=ship.pk).update(belongs_to_crew=False)
    ship.belongs_to_crew=True
    ship.full_clean(); ship.save(update_fields=['belongs_to_crew','updated_at']); return ship
@transaction.atomic
def damage_ship(*,user,campaign,ship,raw_damage:int,resistance_reduction:int=0,final_damage:int|None=None)->Ship:
    _authorize(user,campaign,ship); locked=Ship.objects.select_for_update().get(pk=ship.pk)
    damage=max(0,final_damage if final_damage is not None else raw_damage-resistance_reduction); locked.current_hp=max(0,locked.current_hp-damage); locked.save(update_fields=['current_hp','updated_at']); return locked
@transaction.atomic
def repair_ship(*,user,campaign,ship,amount:int)->Ship:
    _authorize(user,campaign,ship); locked=Ship.objects.select_for_update().get(pk=ship.pk); locked.current_hp=min(locked.max_hp,locked.current_hp+max(0,amount)); locked.save(update_fields=['current_hp','updated_at']); return locked
@transaction.atomic
def update_navigation_resources(*,user,campaign,ship,level:str)->Ship:
    _authorize(user,campaign,ship)
    if level not in dict(NAVIGATION_RESOURCE_LEVELS): raise ValidationError('Nível inválido.')
    ship.navigation_resources=level; ship.save(update_fields=['navigation_resources','updated_at']); return ship
def update_ship_crew(*,user,campaign,ship,current_crew:int)->Ship:
    _authorize(user,campaign,ship); ship.current_crew=current_crew; ship.full_clean(); ship.save(update_fields=['current_crew','updated_at']); return ship
