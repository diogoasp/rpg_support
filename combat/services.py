from collections.abc import Iterable
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from .models import Combat, Combatant, HPChange


class CombatDomainError(ValidationError): pass


def _authorize(*, user, campaign):
    if user is not None and (not user.is_authenticated or not user.is_master or campaign.master_id != user.pk): raise PermissionDenied


@transaction.atomic
def create_combatants_from_encounter(*, combat):
    if combat.combatants.exists(): return list(combat.combatants.all())
    result=[]; order=0
    for group in combat.encounter.enemy_groups.select_related("enemy").order_by("sort_order", "pk"):
        for number in range(1, group.quantity + 1):
            name=group.effective_name + (f" {number}" if group.quantity > 1 else "")
            hp=group.max_hp_override or group.enemy.max_hp
            item=Combatant(combat=combat, enemy=group.enemy, combatant_type="enemy", display_name=name, max_hp=hp, current_hp=hp, armor_class=group.armor_class_override or group.enemy.armor_class, resistance_bonus=group.resistance_bonus_override if group.resistance_bonus_override is not None else group.enemy.resistance_bonus, initiative=group.enemy.initiative, turn_order=order, is_boss=group.is_boss or group.enemy.is_boss, master_note=group.master_note)
            if group.enemy.image: item.image.name=group.enemy.image.name
            item.full_clean(); item.save(); result.append(item); order += 1
    for participant in combat.encounter.participants.filter(is_active=True).select_related("character"):
        c=participant.character
        item=Combatant(combat=combat, character=c, combatant_type="player", display_name=c.name, max_hp=c.max_hp, current_hp=c.current_hp, max_power_points=c.max_power_points, current_power_points=c.current_power_points, armor_class=c.armor_class, initiative=c.initiative, turn_order=order)
        if c.portrait: item.image.name=c.portrait.name
        item.full_clean(); item.save(); result.append(item); order += 1
    return result


@transaction.atomic
def start_combat_from_encounter(*, encounter, user=None, mode="free", track_player_resources=False):
    _authorize(user=user, campaign=encounter.campaign)
    existing=encounter.combats.filter(status__in=("active", "paused")).first()
    if existing: return existing
    if encounter.status not in ("draft", "ready"): raise CombatDomainError("O encontro não pode ser iniciado neste estado.")
    if Combat.objects.filter(campaign=encounter.campaign, status__in=("active", "paused")).exists(): raise CombatDomainError("A campanha já possui um confronto em andamento.")
    combat=Combat(encounter=encounter, campaign=encounter.campaign, mode=mode, track_player_resources=track_player_resources); combat.full_clean(); combat.save()
    create_combatants_from_encounter(combat=combat)
    encounter.status="started"; encounter.started_at=timezone.now(); encounter.save(update_fields=["status", "started_at", "updated_at"])
    return combat


def _sync_character_hp(combatant):
    if not combatant.character_id:
        return
    character = combatant.character
    current_hp = max(0, min(character.max_hp, combatant.current_hp))
    if character.current_hp == current_hp:
        return
    character.current_hp = current_hp
    character.save(update_fields=["current_hp", "updated_at"])


def _hp_change(combatant, new_hp):
    old=combatant.current_hp; combatant.current_hp=max(0, min(combatant.max_hp, new_hp)); combatant.save(update_fields=["current_hp", "updated_at"]); HPChange.objects.create(combatant=combatant, previous_hp=old, new_hp=combatant.current_hp); _sync_character_hp(combatant); return combatant

@transaction.atomic
def apply_damage_to_combatant(*, combatant, raw_damage=None, reduction=0, final_damage=None, mark_defeated_at_zero=True):
    damage=final_damage if final_damage is not None else max(0, (raw_damage or 0)-reduction)
    if damage < 0: raise CombatDomainError("O dano não pode ser negativo.")
    _hp_change(combatant, combatant.current_hp-damage)
    if combatant.current_hp == 0 and mark_defeated_at_zero: combatant.is_defeated=True; combatant.is_active=False; combatant.save(update_fields=["is_defeated", "is_active", "updated_at"])
    return combatant

@transaction.atomic
def heal_combatant(*, combatant, amount):
    if amount < 0: raise CombatDomainError("A cura não pode ser negativa.")
    return _hp_change(combatant, combatant.current_hp+amount)

def change_combatant_state(*, combatant, state, custom_text=""):
    combatant.narrative_state=state; combatant.custom_narrative_state=custom_text if state == "special" else ""; combatant.save(update_fields=["narrative_state", "custom_narrative_state", "updated_at"]); return combatant
def mark_combatant_defeated(*, combatant): combatant.is_defeated=True; combatant.is_active=False; combatant.narrative_state="defeated"; combatant.save(); return combatant
def reactivate_combatant(*, combatant): combatant.is_defeated=False; combatant.is_active=True; combatant.narrative_state=""; combatant.save(); return combatant
def update_combatant_note(*, combatant, note): combatant.master_note=note; combatant.save(update_fields=["master_note", "updated_at"]); return combatant
def change_combat_mode(*, combat, mode):
    combat.mode=mode; combat.current_turn_index=0
    combat.save(update_fields=["mode", "current_turn_index", "updated_at"])
    if mode == "initiative":
        ordered=combat.combatants.order_by("-initiative", "turn_order", "pk")
        set_combat_order(combat=combat, combatant_ids=[x.pk for x in ordered])
    return combat

@transaction.atomic
def set_combat_order(*, combat, combatant_ids: Iterable[int]):
    items={x.pk:x for x in combat.combatants.filter(pk__in=combatant_ids)}
    for index, pk in enumerate(combatant_ids):
        if pk not in items: raise CombatDomainError("Combatente inválido na ordem.")
        items[pk].turn_order=index; items[pk].save(update_fields=["turn_order"])
    return combat

def advance_combat_turn(*, combat, direction=1):
    if combat.mode == "free": return combat
    count=combat.combatants.filter(is_active=True).count()
    if not count: return combat
    old=combat.current_turn_index; combat.current_turn_index=(old+direction)%count
    if combat.mode == "initiative" and direction > 0 and combat.current_turn_index == 0: combat.round_number += 1
    combat.save(update_fields=["current_turn_index", "round_number", "updated_at"]); return combat
def pause_combat(*, combat): combat.status="paused"; combat.save(update_fields=["status", "updated_at"]); return combat
def resume_combat(*, combat): combat.status="active"; combat.save(update_fields=["status", "updated_at"]); return combat
def finish_combat(*, combat, result="", final_note=""):
    combat.status="finished"; combat.result=result; combat.final_note=final_note; combat.finished_at=timezone.now(); combat.save(); combat.encounter.status="finished"; combat.encounter.finished_at=combat.finished_at; combat.encounter.save(update_fields=["status", "finished_at", "updated_at"]); return combat
def reopen_combat(*, combat): combat.status="active"; combat.finished_at=None; combat.save(update_fields=["status", "finished_at", "updated_at"]); combat.encounter.status="started"; combat.encounter.finished_at=None; combat.encounter.save(update_fields=["status", "finished_at", "updated_at"]); return combat
def undo_last_hp_change(*, combatant):
    event=combatant.hp_changes.filter(is_reverted=False).first()
    if not event: raise CombatDomainError("Não há ajuste de PV para desfazer.")
    combatant.current_hp=event.previous_hp; combatant.save(update_fields=["current_hp", "updated_at"]); event.is_reverted=True; event.save(update_fields=["is_reverted"]); _sync_character_hp(combatant); return combatant
