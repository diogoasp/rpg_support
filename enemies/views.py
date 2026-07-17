from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404,redirect,render
from .forms import EnemyForm,EnemyActionFormSet,EnemyFeatureFormSet
from .models import Enemy,EnemyFaction,ENEMY_CATEGORIES,ENEMY_ENVIRONMENTS,OPERATIONAL_COMPLEXITY,ENCOUNTER_MODES
def master(request):
 if not request.user.is_master: raise PermissionDenied
@login_required
def enemy_list(request):
 master(request); q=Enemy.objects.select_related('faction'); mapping={'category':'category','faction':'faction_id','environment':'environment','complexity':'operational_complexity','mode':'encounter_mode','boss':'is_boss','available':'is_available_for_generator'}
 if request.GET.get('q'):q=q.filter(name__icontains=request.GET['q'])
 for key,field in mapping.items():
  if request.GET.get(key)!='' and request.GET.get(key) is not None:q=q.filter(**{field:request.GET[key]})
 return render(request,'enemies/list.html',{'enemies':Paginator(q,20).get_page(request.GET.get('page')),'factions':EnemyFaction.objects.filter(is_active=True),'categories':ENEMY_CATEGORIES,'environments':ENEMY_ENVIRONMENTS,'complexities':OPERATIONAL_COMPLEXITY,'modes':ENCOUNTER_MODES})
@login_required
def detail(request,pk): master(request); return render(request,'enemies/detail.html',{'enemy':get_object_or_404(Enemy.objects.select_related('faction').prefetch_related('actions','features'),pk=pk)})
@login_required
@transaction.atomic
def edit(request,pk=None):
 master(request); obj=get_object_or_404(Enemy,pk=pk) if pk else Enemy(); form=EnemyForm(request.POST or None,request.FILES or None,instance=obj); actions=EnemyActionFormSet(request.POST or None,instance=obj,prefix='actions'); features=EnemyFeatureFormSet(request.POST or None,instance=obj,prefix='features')
 if request.method=='POST' and form.is_valid() and actions.is_valid() and features.is_valid(): obj=form.save(commit=False); obj.full_clean(); obj.save(); actions.instance=obj; actions.save(); features.instance=obj; features.save(); return redirect('enemies:detail',pk=obj.pk)
 return render(request,'enemies/form.html',{'form':form,'actions':actions,'features':features,'enemy':obj})
@login_required
def deactivate(request,pk):
 master(request)
 if request.method=='POST': Enemy.objects.filter(pk=pk).update(is_active=False,is_available_for_generator=False)
 return redirect('enemies:list')
