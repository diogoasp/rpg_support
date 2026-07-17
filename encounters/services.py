from dataclasses import dataclass, field
from decimal import Decimal
import random
from typing import Iterable
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import QuerySet
from .balance import get_balance
from .models import Encounter,EncounterEnemy,EncounterParticipant
from enemies.models import Enemy

@dataclass(frozen=True)
class PartySnapshot:
    size:int; average_level:float; total_level:int; average_max_hp:float; average_armor_class:float; average_power_points:float=0
@dataclass
class SelectedEnemy:
    enemy:Enemy; quantity:int=1; display_name:str=''; max_hp_override:int|None=None; is_boss:bool=False
@dataclass
class GenerateEncounterInput:
    campaign:object; participants:Iterable; difficulty:str; approximate_enemy_count:int; has_boss:bool=False; faction:object|None=None; environment:str=''; required_enemy:Enemy|None=None; notes:str=''
@dataclass
class GeneratedEncounterProposal:
    party_snapshot:PartySnapshot; budget:Decimal; estimated_threat:Decimal; estimated_difficulty:str; selected_enemies:list[SelectedEnemy]; warnings:list[str]=field(default_factory=list); relaxed_filters:list[str]=field(default_factory=list); operational_load:int=0

def build_party_snapshot(characters)->PartySnapshot:
    chars=list(characters)
    if not chars: raise ValidationError('Selecione ao menos um participante.')
    def avg(attr):
        vals=[getattr(c,attr,None) for c in chars]; vals=[v for v in vals if v is not None]
        return round(sum(vals)/len(vals),2) if vals else 0
    return PartySnapshot(len(chars),avg('level'),sum((getattr(c,'level',0) or 0) for c in chars),avg('max_hp'),avg('armor_class'),avg('max_power_points'))
def enemy_threat_score(enemy:Enemy,max_hp_override=None)->Decimal:
    if enemy.threat_score_override is not None and max_hp_override is None:return enemy.threat_score_override
    hp=Decimal(max_hp_override or enemy.max_hp)/Decimal('5'); cr=enemy.challenge_rating*Decimal('4'); defense=Decimal(max(enemy.armor_class-8,0)+max(enemy.resistance_bonus,0))*Decimal('.8'); actions=Decimal(enemy.actions.filter(is_active=True).count())*Decimal('1.5'); complexity=Decimal(get_balance()['complexity_weights'][enemy.operational_complexity]); category=Decimal('1.15') if enemy.category=='elite' else Decimal('1'); boss=Decimal('1.3') if enemy.is_boss else Decimal('1')
    return ((hp+cr+defense+actions+complexity)*category*boss).quantize(Decimal('.01'))
def calculate_encounter_budget(party:PartySnapshot,difficulty:str)->Decimal:
    if difficulty not in get_balance()['difficulty_multipliers']: raise ValidationError('Dificuldade inválida.')
    base=Decimal(str(party.total_level*6+party.average_max_hp*party.size*.35+party.average_armor_class*party.size*.2))
    return (base*Decimal(str(get_balance()['difficulty_multipliers'][difficulty]))).quantize(Decimal('.01'))
def calculate_action_economy_multiplier(quantity:int)->Decimal:
    for limit,value in get_balance()['action_economy_multipliers']:
        if quantity<=limit:return Decimal(str(value))
    return Decimal(str(get_balance()['action_economy_multipliers'][-1][1]))
def calculate_operational_load(selected)->int:return sum(get_balance()['complexity_weights'][x.enemy.operational_complexity]*x.quantity for x in selected)
def estimate_encounter_difficulty(threat,budget):
    ratio=Decimal(threat)/Decimal(budget or 1)
    return 'easy' if ratio<Decimal('.8') else ('medium' if ratio<Decimal('1.2') else 'hard')
def filter_enemy_candidates(*,party,faction=None,environment='',has_boss=False):
    q=Enemy.objects.filter(is_active=True,is_available_for_generator=True,encounter_mode__in=('normal','reduced'))
    if not has_boss:q=q.filter(is_boss=False)
    if faction:q=q.filter(faction=faction)
    if environment:q=q.filter(environment__in=(environment,'any'))
    return q.filter(recommended_min_level__lte=max(1,int(party.average_level)+1),recommended_max_level__gte=max(1,int(party.average_level)-1))
def _warnings(proposal):
    w=[]; qty=sum(x.quantity for x in proposal.selected_enemies)
    if qty>proposal.party_snapshot.size*get_balance()['action_economy_warning_ratio']:w.append('A quantidade de inimigos pode sobrecarregar a economia de ações.')
    if proposal.operational_load>get_balance()['operational_load_warning']:w.append('Este encontro pode exigir controle excessivo do mestre.')
    return w
def recalculate_encounter_proposal(proposal):
    raw=sum((enemy_threat_score(x.enemy,x.max_hp_override)*x.quantity for x in proposal.selected_enemies),Decimal(0)); qty=sum(x.quantity for x in proposal.selected_enemies); proposal.estimated_threat=(raw*calculate_action_economy_multiplier(qty)).quantize(Decimal('.01')); proposal.operational_load=calculate_operational_load(proposal.selected_enemies); proposal.estimated_difficulty=estimate_encounter_difficulty(proposal.estimated_threat,proposal.budget); proposal.warnings=[w for w in proposal.warnings if 'economia de ações' not in w and 'controle excessivo' not in w]+_warnings(proposal); return proposal
def generate_encounter(data:GenerateEncounterInput,seed:int|None=None)->GeneratedEncounterProposal:
    chars=list(data.participants)
    if any(c.campaign_id!=data.campaign.pk for c in chars):raise ValidationError('Todos os participantes devem pertencer à campanha.')
    party=build_party_snapshot(chars); budget=calculate_encounter_budget(party,data.difficulty); count=min(max(1,data.approximate_enemy_count),get_balance()['max_generated_enemies']); selected=[]; warnings=[]; relaxed=[]
    if data.required_enemy:
        selected.append(SelectedEnemy(data.required_enemy,is_boss=data.required_enemy.is_boss))
        if data.required_enemy.encounter_mode=='narrative':warnings.append('Este inimigo foi marcado como encontro narrativo.')
        if data.required_enemy.encounter_mode=='not_recommended':warnings.append('Este inimigo é considerado inadequado para confronto direto com este grupo.')
        if data.required_enemy.recommended_min_level>party.average_level:warnings.append('O inimigo está acima da faixa recomendada do grupo.')
        if enemy_threat_score(data.required_enemy)>budget:warnings.append('O inimigo excede sozinho o orçamento estimado.')
    candidates=list(filter_enemy_candidates(party=party,faction=data.faction,environment=data.environment,has_boss=data.has_boss).exclude(pk=getattr(data.required_enemy,'pk',None)))
    if not candidates and data.environment: relaxed.append('ambiente'); candidates=list(filter_enemy_candidates(party=party,faction=data.faction,has_boss=data.has_boss))
    if not candidates and data.faction: relaxed.append('facção'); candidates=list(filter_enemy_candidates(party=party,has_boss=data.has_boss))
    rng=random.Random(seed); rng.shuffle(candidates)
    if data.has_boss and not any(x.is_boss for x in selected):
        leader=next((e for e in candidates if e.is_boss),None) or next((e for e in candidates if e.category=='elite'),None)
        if leader:selected.append(SelectedEnemy(leader,is_boss=True)); candidates.remove(leader)
    candidates=[e for e in candidates if not e.is_boss] if not data.has_boss else candidates
    while len(selected)<count and candidates:
        selected.append(SelectedEnemy(candidates[(len(selected)-1)%len(candidates)]))
    p=GeneratedEncounterProposal(party,budget,Decimal(0),'easy',selected,warnings,relaxed); return recalculate_encounter_proposal(p)
@transaction.atomic
def save_generated_encounter(*,actor,campaign,name,status,difficulty,proposal,generation_parameters=None,master_notes=''):
    if not actor.is_master or campaign.master_id!=actor.pk:raise PermissionDenied
    if status not in ('draft','ready'):raise ValidationError('Status indisponível nesta fase.')
    parameters=dict(generation_parameters or {}); participants=parameters.pop('_participant_objects',[])
    obj=Encounter.objects.create(campaign=campaign,name=name,difficulty=difficulty,status=status,has_boss=any(x.is_boss for x in proposal.selected_enemies),estimated_difficulty=proposal.estimated_difficulty,estimated_threat=proposal.estimated_threat,operational_load=proposal.operational_load,generator_notes='\n'.join(proposal.warnings),generation_parameters=parameters,master_notes=master_notes,created_by=actor)
    EncounterParticipant.objects.bulk_create([EncounterParticipant(encounter=obj,character=c) for c in participants])
    EncounterEnemy.objects.bulk_create([EncounterEnemy(encounter=obj,enemy=x.enemy,display_name=x.display_name,quantity=x.quantity,max_hp_override=x.max_hp_override,is_boss=x.is_boss,sort_order=i) for i,x in enumerate(proposal.selected_enemies)])
    return obj
@transaction.atomic
def duplicate_encounter(*,actor,encounter):
    if encounter.campaign.master_id!=actor.pk:raise PermissionDenied
    old=encounter; copy=Encounter.objects.create(campaign=old.campaign,name=f'{old.name} — Cópia',difficulty=old.difficulty,status='draft',has_boss=old.has_boss,environment=old.environment,faction=old.faction,estimated_difficulty=old.estimated_difficulty,estimated_threat=old.estimated_threat,operational_load=old.operational_load,generator_notes=old.generator_notes,master_notes=old.master_notes,generation_parameters=old.generation_parameters,created_by=actor)
    EncounterParticipant.objects.bulk_create([EncounterParticipant(encounter=copy,character=x.character,is_active=x.is_active) for x in old.participants.select_related('character')]); EncounterEnemy.objects.bulk_create([EncounterEnemy(encounter=copy,enemy=x.enemy,display_name=x.display_name,quantity=x.quantity,max_hp_override=x.max_hp_override,armor_class_override=x.armor_class_override,resistance_bonus_override=x.resistance_bonus_override,is_boss=x.is_boss,sort_order=x.sort_order,master_note=x.master_note) for x in old.enemy_groups.select_related('enemy')]); return copy
