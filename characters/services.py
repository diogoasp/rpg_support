from typing import Any
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from .models import Character, CharacterChangeLog, CharacterCondition, CharacterFeature, CharacterRecordSource, CharacterTechnique, CharacterWeapon

def ensure_master(user: Any, character: Character)->None:
    if not user.is_authenticated or not user.is_master or character.campaign.master_id != user.pk: raise PermissionDenied
def ensure_owner(user: Any, character: Character)->None:
    if not user.is_authenticated or not user.is_player or character.user_id != user.pk or not character.campaign.players.filter(pk=user.pk).exists(): raise PermissionDenied
def ensure_master_or_owner(user: Any, character: Character)->None:
    if user.is_authenticated and user.is_master and character.campaign.master_id == user.pk: return
    ensure_owner(user,character)
def sync_active_combatants(character: Character)->None:
    from combat.models import Combatant
    Combatant.objects.filter(character=character,combat__status__in=('active','paused')).update(current_hp=character.current_hp)
def validate_resource_bounds(character: Character)->None:
    if character.current_hp > character.max_hp: raise ValidationError('PV atual não pode exceder o máximo.')
    if character.current_power_points > character.max_power_points: raise ValidationError('PP atual não pode exceder o máximo.')
def log_character_change(*,character:Character,user:Any,action:str,object_type:str,object_id:Any='',description:str,old_value:dict|None=None,new_value:dict|None=None)->CharacterChangeLog:
    return CharacterChangeLog.objects.create(character=character,user=user if getattr(user,'is_authenticated',False) else None,action=action,object_type=object_type,object_id=str(object_id or ''),description=description,old_value=old_value or {},new_value=new_value or {})
def _snapshot(obj:Any,fields:tuple[str,...])->dict:
    return {field:getattr(obj,field) for field in fields}
@transaction.atomic
def update_character_resources(*,actor:Any,character:Character,hp:int|None=None,power_points:int|None=None)->Character:
    ensure_master(actor,character); locked=Character.objects.select_for_update().get(pk=character.pk)
    if hp is not None:
        if not 0<=hp<=locked.max_hp: raise ValidationError('PV fora dos limites.')
        locked.current_hp=hp
    if power_points is not None:
        if not 0<=power_points<=locked.max_power_points: raise ValidationError('PP fora dos limites.')
        locked.current_power_points=power_points
    validate_resource_bounds(locked); locked.save(); sync_active_combatants(locked); return locked
@transaction.atomic
def damage_character(*,actor:Any,character:Character,amount:int)->Character:
    ensure_master_or_owner(actor,character)
    if amount < 1: raise ValidationError('O dano deve ser maior que zero.')
    locked=Character.objects.select_for_update().get(pk=character.pk)
    old_hp=locked.current_hp
    locked.current_hp=max(0,locked.current_hp-amount)
    validate_resource_bounds(locked); locked.save(update_fields=('current_hp','updated_at')); sync_active_combatants(locked)
    log_character_change(character=locked,user=actor,action='damage',object_type='resource',description=f'PV {old_hp} → {locked.current_hp}',old_value={'current_hp':old_hp},new_value={'current_hp':locked.current_hp})
    return locked
@transaction.atomic
def heal_character(*,actor:Any,character:Character,amount:int)->Character:
    ensure_master_or_owner(actor,character)
    if amount < 1: raise ValidationError('A cura deve ser maior que zero.')
    locked=Character.objects.select_for_update().get(pk=character.pk)
    old_hp=locked.current_hp
    locked.current_hp=min(locked.max_hp,locked.current_hp+amount)
    validate_resource_bounds(locked); locked.save(update_fields=('current_hp','updated_at')); sync_active_combatants(locked)
    log_character_change(character=locked,user=actor,action='heal',object_type='resource',description=f'PV {old_hp} → {locked.current_hp}',old_value={'current_hp':old_hp},new_value={'current_hp':locked.current_hp})
    return locked
@transaction.atomic
def spend_power_points(*,actor:Any,character:Character,amount:int)->Character:
    ensure_owner(actor,character)
    if amount < 1: raise ValidationError('O gasto deve ser maior que zero.')
    locked=Character.objects.select_for_update().get(pk=character.pk)
    old_pp=locked.current_power_points
    locked.current_power_points=max(0,locked.current_power_points-amount)
    validate_resource_bounds(locked); locked.save(update_fields=('current_power_points','updated_at'))
    log_character_change(character=locked,user=actor,action='spend_pp',object_type='resource',description=f'PP {old_pp} → {locked.current_power_points}',old_value={'current_power_points':old_pp},new_value={'current_power_points':locked.current_power_points})
    return locked
@transaction.atomic
def recover_power_points(*,actor:Any,character:Character,amount:int)->Character:
    ensure_owner(actor,character)
    if amount < 1: raise ValidationError('A recuperação deve ser maior que zero.')
    locked=Character.objects.select_for_update().get(pk=character.pk)
    old_pp=locked.current_power_points
    locked.current_power_points=min(locked.max_power_points,locked.current_power_points+amount)
    validate_resource_bounds(locked); locked.save(update_fields=('current_power_points','updated_at'))
    log_character_change(character=locked,user=actor,action='recover_pp',object_type='resource',description=f'PP {old_pp} → {locked.current_power_points}',old_value={'current_power_points':old_pp},new_value={'current_power_points':locked.current_power_points})
    return locked
@transaction.atomic
def add_character_condition(*,actor:Any,character:Character,**data)->CharacterCondition:
    ensure_master_or_owner(actor,character); condition=CharacterCondition.objects.create(character=character,**data); log_character_change(character=character,user=actor,action='create',object_type='condition',object_id=condition.pk,description=f'Condição adicionada: {condition.name}',new_value={'name':condition.name,'description':condition.description}); return condition
@transaction.atomic
def deactivate_character_condition(*,actor:Any,condition:CharacterCondition)->CharacterCondition:
    ensure_master_or_owner(actor,condition.character); old={'is_active':condition.is_active}; condition.is_active=False; condition.save(update_fields=('is_active','updated_at')); log_character_change(character=condition.character,user=actor,action='deactivate',object_type='condition',object_id=condition.pk,description=f'Condição removida: {condition.name}',old_value=old,new_value={'is_active':False}); return condition

TECHNIQUE_FIELDS=('name','source','description','action_type','range_text','damage_text','damage_die','attribute_modifier','required_weapon_type','power_points_cost','category','technique_type','is_available','is_featured','sort_order')
WEAPON_FIELDS=('name','range_text','damage_die','attribute_modifier','weapon_type','is_available','sort_order')
FEATURE_FIELDS=('name','description','source','is_available','sort_order')

def _require_player_editable(obj:Any)->None:
    if not getattr(obj,'is_player_editable',False): raise PermissionDenied
@transaction.atomic
def create_player_technique(*,actor:Any,character:Character,**data)->CharacterTechnique:
    ensure_owner(actor,character); technique=CharacterTechnique(character=character,source_type=CharacterRecordSource.PLAYER,created_by=actor,**data); technique.full_clean(); technique.save(); log_character_change(character=character,user=actor,action='create',object_type='technique',object_id=technique.pk,description=f'Técnica criada: {technique.name}',new_value=_snapshot(technique,TECHNIQUE_FIELDS)); return technique
@transaction.atomic
def update_player_technique(*,actor:Any,technique:CharacterTechnique,**data)->CharacterTechnique:
    ensure_owner(actor,technique.character); _require_player_editable(technique); old=_snapshot(technique,TECHNIQUE_FIELDS)
    for field,value in data.items(): setattr(technique,field,value)
    technique.full_clean(); technique.save(); log_character_change(character=technique.character,user=actor,action='update',object_type='technique',object_id=technique.pk,description=f'Técnica editada: {technique.name}',old_value=old,new_value=_snapshot(technique,TECHNIQUE_FIELDS)); return technique
@transaction.atomic
def delete_player_technique(*,actor:Any,technique:CharacterTechnique)->CharacterTechnique:
    ensure_owner(actor,technique.character); _require_player_editable(technique); old=_snapshot(technique,TECHNIQUE_FIELDS); technique.is_available=False; technique.save(update_fields=('is_available','updated_at')); log_character_change(character=technique.character,user=actor,action='delete',object_type='technique',object_id=technique.pk,description=f'Técnica removida: {technique.name}',old_value=old,new_value={'is_available':False}); return technique
@transaction.atomic
def duplicate_player_technique(*,actor:Any,technique:CharacterTechnique)->CharacterTechnique:
    ensure_owner(actor,technique.character); data=_snapshot(technique,TECHNIQUE_FIELDS); data['name']=f"{technique.name} (cópia)"; data['is_available']=True; return create_player_technique(actor=actor,character=technique.character,**data)
@transaction.atomic
def create_player_weapon(*,actor:Any,character:Character,**data)->CharacterWeapon:
    ensure_owner(actor,character); weapon=CharacterWeapon(character=character,source_type=CharacterRecordSource.PLAYER,created_by=actor,is_proficient=False,**data); weapon.full_clean(); weapon.save(); log_character_change(character=character,user=actor,action='create',object_type='weapon',object_id=weapon.pk,description=f'Arma criada: {weapon.name}',new_value=_snapshot(weapon,WEAPON_FIELDS)); return weapon
@transaction.atomic
def update_player_weapon(*,actor:Any,weapon:CharacterWeapon,**data)->CharacterWeapon:
    ensure_owner(actor,weapon.character); _require_player_editable(weapon); old=_snapshot(weapon,WEAPON_FIELDS)
    for field,value in data.items(): setattr(weapon,field,value)
    weapon.full_clean(); weapon.save(); log_character_change(character=weapon.character,user=actor,action='update',object_type='weapon',object_id=weapon.pk,description=f'Arma editada: {weapon.name}',old_value=old,new_value=_snapshot(weapon,WEAPON_FIELDS)); return weapon
@transaction.atomic
def delete_player_weapon(*,actor:Any,weapon:CharacterWeapon)->CharacterWeapon:
    ensure_owner(actor,weapon.character); _require_player_editable(weapon); old=_snapshot(weapon,WEAPON_FIELDS); weapon.is_available=False; weapon.save(update_fields=('is_available','updated_at')); log_character_change(character=weapon.character,user=actor,action='delete',object_type='weapon',object_id=weapon.pk,description=f'Arma removida: {weapon.name}',old_value=old,new_value={'is_available':False}); return weapon
@transaction.atomic
def create_player_feature(*,actor:Any,character:Character,**data)->CharacterFeature:
    ensure_owner(actor,character); feature=CharacterFeature(character=character,source_type=CharacterRecordSource.PLAYER,created_by=actor,**data); feature.full_clean(); feature.save(); log_character_change(character=character,user=actor,action='create',object_type='feature',object_id=feature.pk,description=f'Característica criada: {feature.name}',new_value=_snapshot(feature,FEATURE_FIELDS)); return feature
@transaction.atomic
def update_player_feature(*,actor:Any,feature:CharacterFeature,**data)->CharacterFeature:
    ensure_owner(actor,feature.character); _require_player_editable(feature); old=_snapshot(feature,FEATURE_FIELDS)
    for field,value in data.items(): setattr(feature,field,value)
    feature.full_clean(); feature.save(); log_character_change(character=feature.character,user=actor,action='update',object_type='feature',object_id=feature.pk,description=f'Característica editada: {feature.name}',old_value=old,new_value=_snapshot(feature,FEATURE_FIELDS)); return feature
@transaction.atomic
def delete_player_feature(*,actor:Any,feature:CharacterFeature)->CharacterFeature:
    ensure_owner(actor,feature.character); _require_player_editable(feature); old=_snapshot(feature,FEATURE_FIELDS); feature.is_available=False; feature.save(update_fields=('is_available',)); log_character_change(character=feature.character,user=actor,action='delete',object_type='feature',object_id=feature.pk,description=f'Característica removida: {feature.name}',old_value=old,new_value={'is_available':False}); return feature
