from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404,redirect,render
from campaigns.models import Campaign
from .forms import *
from .models import Ship
from .services import create_or_update_ship,damage_ship,repair_ship,update_navigation_resources

def _campaign(request,slug=None):
 if request.user.is_master:
  q=Campaign.objects.filter(slug=slug) if slug else Campaign.objects.all()
 else:
  q=request.user.campaigns.filter(slug=slug) if slug else request.user.campaigns.all()
 c=q.first()
 if not c: raise PermissionDenied
 return c
@login_required
def detail(request):
 c=_campaign(request,request.GET.get('campaign')); return render(request,'ships/detail.html',{'campaign':c,'ship':Ship.objects.filter(campaign=c,is_active=True).first()})
@login_required
def manage(request,slug):
 c=_campaign(request,slug)
 if not request.user.is_master: raise PermissionDenied
 return render(request,'ships/manage.html',{'campaign':c,'ship':Ship.objects.filter(campaign=c,is_active=True).first()})
@login_required
def edit(request,slug):
 c=_campaign(request,slug)
 if not request.user.is_master: raise PermissionDenied
 ship=Ship.objects.filter(campaign=c,is_active=True).first(); form=ShipForm(request.POST or None,request.FILES or None,instance=ship)
 if request.method=='POST' and form.is_valid(): create_or_update_ship(user=request.user,campaign=c,ship=ship,**form.cleaned_data); return redirect('ships:manage',slug=slug)
 return render(request,'ships/form.html',{'form':form,'campaign':c,'ship':ship})
def _action(request,slug,kind):
 c=_campaign(request,slug)
 if not request.user.is_master: raise PermissionDenied
 ship=get_object_or_404(Ship,campaign=c,is_active=True); forms={'damage':DamageShipForm,'repair':RepairShipForm,'resources':NavigationResourcesForm}; form=forms[kind](request.POST or None,**({'instance':ship} if kind=='resources' else {}))
 if request.method=='POST' and form.is_valid():
  if kind=='damage': ship=damage_ship(user=request.user,campaign=c,ship=ship,**form.cleaned_data)
  elif kind=='repair': ship=repair_ship(user=request.user,campaign=c,ship=ship,**form.cleaned_data)
  else: ship=update_navigation_resources(user=request.user,campaign=c,ship=ship,level=form.cleaned_data['navigation_resources'])
  return render(request,'ships/partials/card.html',{'ship':ship,'campaign':c,'is_master':True})
 return render(request,'ships/partials/action_form.html',{'form':form,'campaign':c,'ship':ship,'kind':kind})
@login_required
def damage(request,slug): return _action(request,slug,'damage')
@login_required
def repair(request,slug): return _action(request,slug,'repair')
@login_required
def resources(request,slug): return _action(request,slug,'resources')
