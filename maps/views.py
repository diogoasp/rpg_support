from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import FileResponse,Http404
from django.shortcuts import get_object_or_404,redirect,render
from campaigns.models import Campaign
from .forms import CampaignMapForm,MapVisibilityForm
from .models import CampaignMap
from .services import create_campaign_map,change_map_visibility,deactivate_campaign_map
def campaigns_for(user): return Campaign.objects.filter(master=user) if user.is_master else user.campaigns.all()
def allowed(user):
 q=CampaignMap.objects.filter(campaign__in=campaigns_for(user),is_active=True)
 if user.is_master:return q
 return q.filter(is_visible_to_players=True).filter(Q(visible_to_users=user)|Q(visible_to_users__isnull=True)).distinct()
@login_required
def player_list(request):
 q=allowed(request.user); t=request.GET.get('type'); q=q.filter(map_type=t) if t else q
 return render(request,'maps/list.html',{'maps':q.prefetch_related('visible_to_users'),'types':CampaignMap._meta.get_field('map_type').choices})
@login_required
def master_list(request,slug):
 c=get_object_or_404(Campaign,slug=slug,master=request.user); q=CampaignMap.objects.filter(campaign=c).prefetch_related('visible_to_users'); search=request.GET.get('q'); q=q.filter(title__icontains=search) if search else q
 return render(request,'maps/master_list.html',{'campaign':c,'maps':q})
@login_required
def edit(request,slug,pk=None):
 c=get_object_or_404(Campaign,slug=slug,master=request.user); obj=get_object_or_404(CampaignMap,pk=pk,campaign=c) if pk else None; form=CampaignMapForm(request.POST or None,request.FILES or None,instance=obj)
 if request.method=='POST' and form.is_valid():
  users=form.cleaned_data.pop('visible_to_users',()); create_campaign_map(user=request.user,campaign=c,instance=obj,visible_to_users=users,**form.cleaned_data); return redirect('maps:master_list',slug=slug)
 return render(request,'maps/form.html',{'campaign':c,'form':form,'object':obj})
@login_required
def visibility(request,slug,pk):
 c=get_object_or_404(Campaign,slug=slug,master=request.user); obj=get_object_or_404(CampaignMap,pk=pk,campaign=c); form=MapVisibilityForm(request.POST or None,instance=obj)
 if request.method=='POST' and form.is_valid(): obj=change_map_visibility(user=request.user,campaign=c,campaign_map=obj,is_visible=form.cleaned_data['is_visible_to_players'],visible_to_users=form.cleaned_data['visible_to_users']); return render(request,'maps/partials/card.html',{'map':obj,'campaign':c,'is_master':True})
 return render(request,'maps/partials/visibility_form.html',{'form':form,'map':obj,'campaign':c})
@login_required
def deactivate(request,slug,pk):
 if request.method!='POST': raise Http404
 c=get_object_or_404(Campaign,slug=slug,master=request.user); obj=get_object_or_404(CampaignMap,pk=pk,campaign=c); deactivate_campaign_map(user=request.user,campaign=c,campaign_map=obj); return redirect('maps:master_list',slug=slug)
@login_required
def protected_file(request,pk,kind):
 obj=get_object_or_404(allowed(request.user),pk=pk); field=obj.image if kind=='image' else obj.file
 if not field: raise Http404
 return FileResponse(field.open('rb'),as_attachment=kind=='file',filename=field.name.rsplit('/',1)[-1])
