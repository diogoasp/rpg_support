from math import ceil
from typing import Any
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from .models import Character, CharacterChangeLog, CharacterCondition, CharacterFeature, CharacterRecordSource, CharacterTechnique, CharacterTechniqueActivation, CharacterTechniqueGrade, CharacterTechniqueUse, CharacterWeapon

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
def use_player_technique(*,actor:Any,technique:CharacterTechnique,grade:int|None=None)->CharacterTechniqueUse:
    ensure_owner(actor,technique.character)
    locked_technique=CharacterTechnique.objects.select_for_update().select_related('character').get(pk=technique.pk)
    if not locked_technique.is_available: raise ValidationError('Técnica indisponível.')
    if locked_technique.usage_mode==CharacterTechnique.UsageMode.CONTINUOUS:
        return activate_continuous_technique(actor=actor,technique=locked_technique)
    if locked_technique.usage_mode==CharacterTechnique.UsageMode.GRADED:
        if grade is None: raise ValidationError('Escolha o grau da técnica.')
        selected_grade=get_object_or_validation_error(locked_technique,grade)
        grade=selected_grade.grade
        cost=selected_grade.power_points_cost
    else:
        if grade is not None: raise ValidationError('Esta técnica não utiliza graus.')
        cost=locked_technique.power_points_cost or 0
    locked=Character.objects.select_for_update().get(pk=technique.character_id)
    if cost and locked.current_power_points < cost:
        raise ValidationError(f'PP insuficiente. Necessário: {cost}. Disponível: {locked.current_power_points}.')
    old_pp=locked.current_power_points
    if cost:
        locked.current_power_points=max(0,locked.current_power_points-cost)
        validate_resource_bounds(locked)
        locked.save(update_fields=('current_power_points','updated_at'))
    use=CharacterTechniqueUse.objects.create(technique=locked_technique,kind=CharacterTechniqueUse.Kind.USE,grade=grade,power_points_spent=cost,used_by=actor)
    grade_label=f' no Grau {grade}' if grade is not None else ''
    log_character_change(character=locked,user=actor,action='use_technique',object_type='technique',object_id=technique.pk,description=f'{technique.name} usada{grade_label} · -{cost} PP',old_value={'current_power_points':old_pp},new_value={'current_power_points':locked.current_power_points,'technique_use_id':use.pk,'grade':grade})
    return use

def get_object_or_validation_error(technique:CharacterTechnique,grade:int)->CharacterTechniqueGrade:
    try:
        normalized=int(grade)
    except (TypeError,ValueError):
        raise ValidationError('Grau inválido.')
    try:
        return technique.grades.get(grade=normalized)
    except CharacterTechniqueGrade.DoesNotExist:
        raise ValidationError('Grau indisponível para esta técnica.')

@transaction.atomic
def activate_continuous_technique(*,actor:Any,technique:CharacterTechnique)->CharacterTechniqueUse:
    ensure_owner(actor,technique.character)
    locked_technique=CharacterTechnique.objects.select_for_update().select_related('character').get(pk=technique.pk)
    if not locked_technique.is_available: raise ValidationError('Técnica indisponível.')
    if locked_technique.usage_mode!=CharacterTechnique.UsageMode.CONTINUOUS: raise ValidationError('Esta técnica não possui efeito contínuo.')
    if locked_technique.activations.filter(status=CharacterTechniqueActivation.Status.ACTIVE).exists(): raise ValidationError('Esta técnica já está ativa.')
    locked=Character.objects.select_for_update().get(pk=locked_technique.character_id)
    cost=locked_technique.power_points_cost or 0
    if locked.current_power_points < cost: raise ValidationError(f'PP insuficiente. Necessário: {cost}. Disponível: {locked.current_power_points}.')
    old_pp=locked.current_power_points
    locked.current_power_points-=cost
    validate_resource_bounds(locked); locked.save(update_fields=('current_power_points','updated_at'))
    activation=CharacterTechniqueActivation.objects.create(technique=locked_technique,activated_by=actor,activation_cost=cost,maintenance_cost=1)
    use=CharacterTechniqueUse.objects.create(technique=locked_technique,activation=activation,kind=CharacterTechniqueUse.Kind.ACTIVATE,power_points_spent=cost,used_by=actor)
    log_character_change(character=locked,user=actor,action='activate_technique',object_type='technique',object_id=technique.pk,description=f'{technique.name} ativada · -{cost} PP',old_value={'current_power_points':old_pp},new_value={'current_power_points':locked.current_power_points,'technique_use_id':use.pk,'activation_id':activation.pk})
    return use

@transaction.atomic
def maintain_continuous_technique(*,actor:Any,technique:CharacterTechnique)->CharacterTechniqueUse:
    ensure_owner(actor,technique.character)
    locked_technique=CharacterTechnique.objects.select_for_update().select_related('character').get(pk=technique.pk)
    activation=locked_technique.activations.select_for_update().filter(status=CharacterTechniqueActivation.Status.ACTIVE).first()
    if not activation: raise ValidationError('Esta técnica não está ativa.')
    locked=Character.objects.select_for_update().get(pk=locked_technique.character_id)
    cost=activation.maintenance_cost
    if locked.current_power_points < cost: raise ValidationError(f'PP insuficiente. Necessário: {cost}. Disponível: {locked.current_power_points}.')
    old_pp=locked.current_power_points
    locked.current_power_points-=cost
    locked.save(update_fields=('current_power_points','updated_at'))
    activation.rounds_maintained+=1
    activation.save(update_fields=('rounds_maintained',))
    use=CharacterTechniqueUse.objects.create(technique=locked_technique,activation=activation,kind=CharacterTechniqueUse.Kind.MAINTAIN,power_points_spent=cost,used_by=actor)
    log_character_change(character=locked,user=actor,action='maintain_technique',object_type='technique',object_id=technique.pk,description=f'{technique.name} mantida por mais uma rodada · -{cost} PP',old_value={'current_power_points':old_pp},new_value={'current_power_points':locked.current_power_points,'technique_use_id':use.pk,'rounds_maintained':activation.rounds_maintained})
    return use

@transaction.atomic
def end_continuous_technique(*,actor:Any,technique:CharacterTechnique)->CharacterTechniqueActivation:
    ensure_owner(actor,technique.character)
    locked_technique=CharacterTechnique.objects.select_for_update().get(pk=technique.pk)
    activation=locked_technique.activations.select_for_update().filter(status=CharacterTechniqueActivation.Status.ACTIVE).first()
    if not activation: raise ValidationError('Esta técnica não está ativa.')
    activation.status=CharacterTechniqueActivation.Status.ENDED
    activation.ended_at=timezone.now()
    activation.save(update_fields=('status','ended_at'))
    log_character_change(character=technique.character,user=actor,action='end_technique',object_type='technique',object_id=technique.pk,description=f'{technique.name} encerrada',old_value={'active':True},new_value={'active':False,'rounds_maintained':activation.rounds_maintained})
    return activation

@transaction.atomic
def undo_player_technique_use(*,actor:Any,technique:CharacterTechnique)->CharacterTechniqueUse:
    ensure_owner(actor,technique.character)
    locked_technique=CharacterTechnique.objects.select_for_update().get(pk=technique.pk)
    use=locked_technique.uses.select_for_update().filter(undone_at__isnull=True).order_by('-created_at').first()
    if not use: raise ValidationError('Não há uso desta técnica para desfazer.')
    locked=Character.objects.select_for_update().get(pk=technique.character_id)
    cost=use.power_points_spent
    old_pp=locked.current_power_points
    if cost:
        locked.current_power_points=min(locked.max_power_points,locked.current_power_points+cost)
        validate_resource_bounds(locked)
        locked.save(update_fields=('current_power_points','updated_at'))
    if use.kind==CharacterTechniqueUse.Kind.ACTIVATE and use.activation:
        if use.activation.status!=CharacterTechniqueActivation.Status.ACTIVE or use.activation.rounds_maintained:
            raise ValidationError('A ativação não pode ser desfeita depois de mantida ou encerrada.')
        use.activation.status=CharacterTechniqueActivation.Status.ENDED
        use.activation.ended_at=timezone.now()
        use.activation.save(update_fields=('status','ended_at'))
    elif use.kind==CharacterTechniqueUse.Kind.MAINTAIN and use.activation:
        use.activation.rounds_maintained=max(0,use.activation.rounds_maintained-1)
        use.activation.save(update_fields=('rounds_maintained',))
    use.undone_at=timezone.now(); use.undone_by=actor; use.save(update_fields=('undone_at','undone_by'))
    log_character_change(character=locked,user=actor,action='undo_technique',object_type='technique',object_id=technique.pk,description=f'Uso desfeito: {technique.name} · +{cost} PP',old_value={'current_power_points':old_pp},new_value={'current_power_points':locked.current_power_points,'technique_use_id':use.pk})
    return use

@transaction.atomic
def short_rest_character(*,actor:Any,character:Character)->Character:
    ensure_owner(actor,character)
    locked=Character.objects.select_for_update().get(pk=character.pk)
    old={'current_hp':locked.current_hp,'current_power_points':locked.current_power_points,'great_damage_recovery_day':locked.great_damage_recovery_day}
    hp_gain=locked.great_damage_recovery_hp_per_rest if locked.great_damage_recovery_days else ceil(locked.max_hp/2)
    locked.current_hp=min(locked.max_hp,locked.current_hp+hp_gain)
    locked.current_power_points=min(locked.max_power_points,locked.current_power_points+ceil(locked.max_power_points/2))
    if locked.great_damage_recovery_days:
        if locked.great_damage_recovery_day >= locked.great_damage_recovery_days:
            locked.great_damage_recovery_days=0; locked.great_damage_recovery_day=0; locked.great_damage_recovery_hp_per_rest=0
        else:
            locked.great_damage_recovery_day+=1
    validate_resource_bounds(locked); locked.save()
    log_character_change(character=locked,user=actor,action='short_rest',object_type='resource',description='Descanso curto aplicado',old_value=old,new_value={'current_hp':locked.current_hp,'current_power_points':locked.current_power_points,'great_damage_recovery_day':locked.great_damage_recovery_day})
    return locked

@transaction.atomic
def long_rest_character(*,actor:Any,character:Character)->Character:
    ensure_owner(actor,character)
    locked=Character.objects.select_for_update().get(pk=character.pk)
    old={'current_hp':locked.current_hp,'current_power_points':locked.current_power_points,'great_damage_recovery_days':locked.great_damage_recovery_days}
    locked.current_hp=locked.max_hp
    locked.current_power_points=locked.max_power_points
    locked.great_damage_recovery_days=0
    locked.great_damage_recovery_day=0
    locked.great_damage_recovery_hp_per_rest=0
    validate_resource_bounds(locked); locked.save()
    log_character_change(character=locked,user=actor,action='long_rest',object_type='resource',description='Descanso longo aplicado',old_value=old,new_value={'current_hp':locked.current_hp,'current_power_points':locked.current_power_points,'great_damage_recovery_days':0})
    return locked

@transaction.atomic
def start_great_damage_recovery(*,actor:Any,character:Character,days:int)->Character:
    ensure_owner(actor,character)
    if days < 1 or days > 30: raise ValidationError('Informe entre 1 e 30 dias.')
    locked=Character.objects.select_for_update().get(pk=character.pk)
    missing_hp=max(0,locked.max_hp-locked.current_hp)
    locked.great_damage_recovery_days=days
    locked.great_damage_recovery_day=1
    locked.great_damage_recovery_hp_per_rest=ceil(missing_hp/days) if missing_hp else 0
    locked.save(update_fields=('great_damage_recovery_days','great_damage_recovery_day','great_damage_recovery_hp_per_rest','updated_at'))
    log_character_change(character=locked,user=actor,action='start_great_damage_recovery',object_type='resource',description=f'Recuperação de grande dano iniciada: {days} dias',new_value={'days':days,'hp_per_rest':locked.great_damage_recovery_hp_per_rest})
    return locked
@transaction.atomic
def add_character_condition(*,actor:Any,character:Character,**data)->CharacterCondition:
    ensure_master_or_owner(actor,character); condition=CharacterCondition.objects.create(character=character,**data); log_character_change(character=character,user=actor,action='create',object_type='condition',object_id=condition.pk,description=f'Condição adicionada: {condition.name}',new_value={'name':condition.name,'description':condition.description}); return condition
@transaction.atomic
def deactivate_character_condition(*,actor:Any,condition:CharacterCondition)->CharacterCondition:
    ensure_master_or_owner(actor,condition.character); old={'is_active':condition.is_active}; condition.is_active=False; condition.save(update_fields=('is_active','updated_at')); log_character_change(character=condition.character,user=actor,action='deactivate',object_type='condition',object_id=condition.pk,description=f'Condição removida: {condition.name}',old_value=old,new_value={'is_active':False}); return condition

TECHNIQUE_FIELDS=('name','source','description','effect_summary','usage_mode','action_type','range_text','damage_text','damage_die','attribute_modifier','required_weapon_type','power_points_cost','category','technique_type','is_available','is_featured','sort_order')
WEAPON_FIELDS=('name','range_text','damage_die','attribute_modifier','weapon_type','is_available','sort_order')
FEATURE_FIELDS=('name','description','source','is_available','sort_order')

def _require_player_editable(obj:Any)->None:
    if not getattr(obj,'is_player_editable',False): raise PermissionDenied

def _replace_technique_grades(technique:CharacterTechnique,grades:list[dict]|None)->None:
    technique.grades.all().delete()
    if technique.usage_mode!=CharacterTechnique.UsageMode.GRADED: return
    normalized={int(item['grade']):item for item in (grades or [])}
    if set(normalized)!={0,1,2}: raise ValidationError('Técnicas em graus exigem efeitos para os Graus 0, 1 e 2.')
    for grade in range(3):
        item=normalized[grade]
        row=CharacterTechniqueGrade(technique=technique,grade=grade,effect_summary=(item.get('effect_summary') or '').strip(),description=item.get('description') or '')
        row.full_clean(); row.save()
@transaction.atomic
def create_player_technique(*,actor:Any,character:Character,grades:list[dict]|None=None,**data)->CharacterTechnique:
    ensure_owner(actor,character); technique=CharacterTechnique(character=character,source_type=CharacterRecordSource.PLAYER,created_by=actor,**data); technique.full_clean(); technique.save(); _replace_technique_grades(technique,grades); log_character_change(character=character,user=actor,action='create',object_type='technique',object_id=technique.pk,description=f'Técnica criada: {technique.name}',new_value={**_snapshot(technique,TECHNIQUE_FIELDS),'grades':grades or []}); return technique
@transaction.atomic
def update_player_technique(*,actor:Any,technique:CharacterTechnique,grades:list[dict]|None=None,**data)->CharacterTechnique:
    ensure_owner(actor,technique.character); _require_player_editable(technique); old=_snapshot(technique,TECHNIQUE_FIELDS)
    for field,value in data.items(): setattr(technique,field,value)
    technique.full_clean(); technique.save(); _replace_technique_grades(technique,grades); log_character_change(character=technique.character,user=actor,action='update',object_type='technique',object_id=technique.pk,description=f'Técnica editada: {technique.name}',old_value=old,new_value={**_snapshot(technique,TECHNIQUE_FIELDS),'grades':grades or []}); return technique
@transaction.atomic
def delete_player_technique(*,actor:Any,technique:CharacterTechnique)->CharacterTechnique:
    ensure_owner(actor,technique.character); _require_player_editable(technique); old=_snapshot(technique,TECHNIQUE_FIELDS); technique.is_available=False; technique.save(update_fields=('is_available','updated_at')); log_character_change(character=technique.character,user=actor,action='delete',object_type='technique',object_id=technique.pk,description=f'Técnica removida: {technique.name}',old_value=old,new_value={'is_available':False}); return technique
@transaction.atomic
def duplicate_player_technique(*,actor:Any,technique:CharacterTechnique)->CharacterTechnique:
    ensure_owner(actor,technique.character); data=_snapshot(technique,TECHNIQUE_FIELDS); data['name']=f"{technique.name} (cópia)"; data['is_available']=True; grades=list(technique.grades.values('grade','effect_summary','description')); return create_player_technique(actor=actor,character=technique.character,grades=grades,**data)
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
