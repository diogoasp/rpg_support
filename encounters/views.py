from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count,Sum
from django.shortcuts import get_object_or_404,redirect,render
from campaigns.models import Campaign
from enemies.models import Enemy
from .forms import GeneratorForm,SaveEncounterForm
from .models import Encounter
from .services import GenerateEncounterInput,GeneratedEncounterProposal,SelectedEnemy,build_party_snapshot,calculate_encounter_budget,duplicate_encounter,generate_encounter,recalculate_encounter_proposal,save_generated_encounter
def campaign_for(request,slug):
 c=get_object_or_404(Campaign,slug=slug)
 if not request.user.is_master or c.master_id!=request.user.pk:raise PermissionDenied
 return c
def serialize(p,data):
 return {'participants':[x.pk for x in data.participants],'difficulty':data.difficulty,'count':data.approximate_enemy_count,'has_boss':data.has_boss,'faction':getattr(data.faction,'pk',None),'environment':data.environment,'notes':data.notes,'selected':[{'enemy':x.enemy.pk,'quantity':x.quantity,'display_name':x.display_name,'hp':x.max_hp_override,'boss':x.is_boss} for x in p.selected_enemies],'warnings':p.warnings,'relaxed':p.relaxed_filters}
def load(c,payload):
 chars=list(c.characters.filter(pk__in=payload['participants'])); snap=build_party_snapshot(chars); selected=[SelectedEnemy(Enemy.objects.get(pk=x['enemy']),x['quantity'],x['display_name'],x['hp'],x['boss']) for x in payload['selected']]; p=GeneratedEncounterProposal(snap,calculate_encounter_budget(snap,payload['difficulty']),Decimal(0),'easy',selected,list(payload['warnings']),list(payload['relaxed'])); return recalculate_encounter_proposal(p),chars
@login_required
def generator(request,slug):
 c=campaign_for(request,slug); form=GeneratorForm(request.POST or None,campaign=c)
 if request.method=='POST' and form.is_valid():
  d=GenerateEncounterInput(campaign=c,participants=form.cleaned_data['participants'],difficulty=form.cleaned_data['difficulty'],approximate_enemy_count=form.cleaned_data['approximate_enemy_count'],has_boss=form.cleaned_data['has_boss'],faction=form.cleaned_data['faction'],environment=form.cleaned_data['environment'],required_enemy=form.cleaned_data['required_enemy'],notes=form.cleaned_data['notes']); p=generate_encounter(d,seed=int(request.POST.get('seed',0))); request.session[f'proposal_{c.pk}']=serialize(p,d); template='encounters/partials/proposal.html' if request.headers.get('HX-Request') else 'encounters/generator.html'; return render(request,template,{'campaign':c,'form':form,'proposal':p,'save_form':SaveEncounterForm()})
 return render(request,'encounters/generator.html',{'campaign':c,'form':form})
@login_required
def revise(request,slug):
 c=campaign_for(request,slug); payload=request.session.get(f'proposal_{c.pk}')
 if not payload: return render(request,'encounters/partials/error.html',{'error':'A proposta expirou.'},status=400)
 idx=int(request.POST.get('index',-1)); action=request.POST.get('action')
 if action=='remove' and 0<=idx<len(payload['selected']):payload['selected'].pop(idx)
 elif action=='quantity' and 0<=idx<len(payload['selected']):payload['selected'][idx]['quantity']=max(1,int(request.POST.get('quantity',1))); payload['selected'][idx]['hp']=int(request.POST['hp']) if request.POST.get('hp') else None; payload['selected'][idx]['display_name']=request.POST.get('display_name',''); payload['selected'][idx]['boss']=request.POST.get('boss')=='on'
 elif action=='add': payload['selected'].append({'enemy':int(request.POST['enemy']),'quantity':1,'display_name':'','hp':None,'boss':False})
 p,_=load(c,payload); request.session[f'proposal_{c.pk}']=payload; return render(request,'encounters/partials/proposal.html',{'campaign':c,'proposal':p,'save_form':SaveEncounterForm(),'all_enemies':Enemy.objects.filter(is_active=True)})
@login_required
def save(request,slug):
 c=campaign_for(request,slug); payload=request.session.get(f'proposal_{c.pk}'); form=SaveEncounterForm(request.POST)
 if not payload or not form.is_valid():return render(request,'encounters/partials/error.html',{'error':'Dados inválidos ou proposta expirada.'},status=400)
 p,chars=load(c,payload); params={k:v for k,v in payload.items() if k not in ('selected','warnings','relaxed')}; params['_participant_objects']=chars; e=save_generated_encounter(actor=request.user,campaign=c,name=form.cleaned_data['name'],status=form.cleaned_data['status'],difficulty=payload['difficulty'],proposal=p,generation_parameters=params,master_notes=form.cleaned_data['master_notes']); request.session.pop(f'proposal_{c.pk}',None); return redirect('encounters:detail',slug=slug,pk=e.pk)
@login_required
def encounter_list(request,slug):
 c=campaign_for(request,slug); q=Encounter.objects.filter(campaign=c).select_related('faction').prefetch_related('participants__character','enemy_groups__enemy')
 for key in ('status','difficulty'):
  if request.GET.get(key):q=q.filter(**{key:request.GET[key]})
 if request.GET.get('boss'):q=q.filter(has_boss=request.GET['boss']=='true')
 return render(request,'encounters/list.html',{'campaign':c,'encounters':q})
@login_required
def detail(request,slug,pk): c=campaign_for(request,slug); return render(request,'encounters/detail.html',{'campaign':c,'encounter':get_object_or_404(Encounter.objects.select_related('faction','created_by').prefetch_related('participants__character','enemy_groups__enemy'),pk=pk,campaign=c)})
@login_required
def duplicate(request,slug,pk): c=campaign_for(request,slug); old=get_object_or_404(Encounter,pk=pk,campaign=c); return redirect('encounters:detail',slug=slug,pk=duplicate_encounter(actor=request.user,encounter=old).pk)
@login_required
def cancel(request,slug,pk): c=campaign_for(request,slug); Encounter.objects.filter(pk=pk,campaign=c,status__in=('draft','ready')).update(status='cancelled'); return redirect('encounters:detail',slug=slug,pk=pk)
