from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from campaigns.models import Campaign
from encounters.models import Encounter
from .forms import DamageForm, FinishCombatForm, HealForm, ModeForm, NoteForm, StartCombatForm, StateForm
from .models import Combat, Combatant
from . import services

def _master(request):
    if not request.user.is_authenticated or not request.user.is_master: raise PermissionDenied
def _combat(request, pk):
    _master(request); return get_object_or_404(Combat.objects.select_related("campaign", "encounter"), pk=pk, campaign__master=request.user)
def _combatant(request, combat_id, pk): return get_object_or_404(Combatant.objects.select_related("combat", "combat__campaign", "enemy", "character").prefetch_related("enemy__actions", "enemy__features"), pk=pk, combat_id=combat_id, combat__campaign__master=request.user)
def _card(request, item): return render(request, "combat/partials/combatant_card.html", {"combat":item.combat, "item":item})

def start(request, slug, pk):
    _master(request); campaign=get_object_or_404(Campaign, slug=slug, master=request.user); encounter=get_object_or_404(Encounter, pk=pk, campaign=campaign)
    form=StartCombatForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        combat=services.start_combat_from_encounter(encounter=encounter, user=request.user, **form.cleaned_data); return redirect("combat:panel", pk=combat.pk)
    return render(request, "combat/start.html", {"campaign":campaign, "encounter":encounter, "form":form})
def panel(request, pk):
    combat=_combat(request, pk); qs=combat.combatants.select_related("enemy", "character")
    q=request.GET.get("q", ""); filter_by=request.GET.get("filter", "all")
    if q: qs=qs.filter(display_name__icontains=q)
    filters={"active":Q(is_active=True), "wounded":Q(narrative_state="wounded")|Q(narrative_state="", current_hp__gt=0, current_hp__lte=models.F("max_hp")/2), "badly_wounded":Q(narrative_state="badly_wounded"), "bosses":Q(is_boss=True), "defeated":Q(is_defeated=True), "resolved":Q(narrative_state__in=("fleeing","surrendered"))}
    if filter_by in filters: qs=qs.filter(filters[filter_by])
    items=list(qs.order_by("-is_boss", "is_defeated", "turn_order", "pk"))
    if combat.mode == "initiative": items.sort(key=lambda x: (-(x.initiative or 0), x.turn_order))
    summary={"active":combat.combatants.filter(combatant_type="enemy",is_active=True).count(),"defeated":combat.combatants.filter(combatant_type="enemy",is_defeated=True).count(),"bosses":combat.combatants.filter(is_boss=True,is_active=True).count(),"participants":combat.combatants.filter(combatant_type="player").count()}
    return render(request, "combat/panel.html", {"combat":combat, "items":items, "filter":filter_by, "q":q,"summary":summary})
def damage(request, combat_id, pk):
    item=_combatant(request,combat_id,pk); form=DamageForm(request.POST or None, initial={"reduction":item.resistance_bonus})
    if request.method=="POST" and form.is_valid(): services.apply_damage_to_combatant(combatant=item, **form.cleaned_data); return _card(request,item)
    return render(request,"combat/partials/form.html",{"form":form,"title":"Aplicar dano","url_name":"combat:damage","item":item,"combat":item.combat})
def heal(request, combat_id, pk):
    item=_combatant(request,combat_id,pk); form=HealForm(request.POST or None)
    if request.method=="POST" and form.is_valid(): services.heal_combatant(combatant=item,**form.cleaned_data); return _card(request,item)
    return render(request,"combat/partials/form.html",{"form":form,"title":"Curar","url_name":"combat:heal","item":item,"combat":item.combat})
def state(request, combat_id, pk):
    item=_combatant(request,combat_id,pk); form=StateForm(request.POST or None,initial={"state":item.effective_narrative_state,"custom_text":item.custom_narrative_state})
    if request.method=="POST" and form.is_valid(): services.change_combatant_state(combatant=item,**form.cleaned_data); return _card(request,item)
    return render(request,"combat/partials/form.html",{"form":form,"title":"Alterar estado","url_name":"combat:state","item":item,"combat":item.combat})
def note(request, combat_id, pk):
    item=_combatant(request,combat_id,pk); form=NoteForm(request.POST or None,initial={"note":item.master_note})
    if request.method=="POST" and form.is_valid(): services.update_combatant_note(combatant=item,**form.cleaned_data); return _card(request,item)
    return render(request,"combat/partials/form.html",{"form":form,"title":"Anotação","url_name":"combat:note","item":item,"combat":item.combat})
@require_POST
def defeat(request,combat_id,pk): item=_combatant(request,combat_id,pk); services.mark_combatant_defeated(combatant=item); return _card(request,item)
@require_POST
def reactivate(request,combat_id,pk): item=_combatant(request,combat_id,pk); services.reactivate_combatant(combatant=item); return _card(request,item)
@require_POST
def undo(request,combat_id,pk): item=_combatant(request,combat_id,pk); services.undo_last_hp_change(combatant=item); return _card(request,item)
def sheet(request,combat_id,pk): item=_combatant(request,combat_id,pk); return render(request,"combat/partials/sheet.html",{"item":item})
@require_POST
def pause(request,pk): combat=_combat(request,pk); services.pause_combat(combat=combat); return redirect("combat:panel",pk=pk)
@require_POST
def resume(request,pk): combat=_combat(request,pk); services.resume_combat(combat=combat); return redirect("combat:panel",pk=pk)
@require_POST
def turn(request,pk): combat=_combat(request,pk); services.advance_combat_turn(combat=combat,direction=int(request.POST.get("direction",1))); return redirect("combat:panel",pk=pk)
def mode(request,pk):
    combat=_combat(request,pk); form=ModeForm(request.POST or None,initial={"mode":combat.mode})
    if request.method=="POST" and form.is_valid(): services.change_combat_mode(combat=combat,**form.cleaned_data); return redirect("combat:panel",pk=pk)
    return render(request,"combat/mode.html",{"combat":combat,"form":form})
def finish(request,pk):
    combat=_combat(request,pk); form=FinishCombatForm(request.POST or None)
    if request.method=="POST" and form.is_valid(): services.finish_combat(combat=combat,**form.cleaned_data); return redirect("combat:panel",pk=pk)
    return render(request,"combat/finish.html",{"combat":combat,"form":form})
@require_POST
def reopen(request,pk): combat=_combat(request,pk); services.reopen_combat(combat=combat); return redirect("combat:panel",pk=pk)
