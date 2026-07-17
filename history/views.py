from django.contrib.auth.decorators import login_required
from django.http import Http404
from config.protected_media import protected_file_response
from django.shortcuts import get_object_or_404,redirect,render
from campaigns.models import Campaign
from .forms import SessionRecordForm,PublicationForm
from .models import SessionRecord
from .services import create_session_record,publish_session_record,unpublish_session_record
def campaigns_for(u): return Campaign.objects.filter(master=u) if u.is_master else u.campaigns.all()
def allowed(u):
 q=SessionRecord.objects.filter(campaign__in=campaigns_for(u)); return q if u.is_master else q.filter(is_published=True)
@login_required
def record_list(request): return render(request,'history/list.html',{'records':allowed(request.user).select_related('campaign')})
@login_required
def detail(request,pk): return render(request,'history/detail.html',{'record':get_object_or_404(allowed(request.user),pk=pk)})
@login_required
def master_list(request,slug):
 c=get_object_or_404(Campaign,slug=slug,master=request.user); return render(request,'history/master_list.html',{'campaign':c,'records':SessionRecord.objects.filter(campaign=c)})
@login_required
def edit(request,slug,pk=None):
 c=get_object_or_404(Campaign,slug=slug,master=request.user); obj=get_object_or_404(SessionRecord,pk=pk,campaign=c) if pk else None; form=SessionRecordForm(request.POST or None,request.FILES or None,instance=obj)
 if request.method=='POST' and form.is_valid(): create_session_record(user=request.user,campaign=c,instance=obj,**form.cleaned_data); return redirect('history:master_list',slug=slug)
 return render(request,'history/form.html',{'form':form,'campaign':c,'object':obj})
@login_required
def publication(request,slug,pk):
 c=get_object_or_404(Campaign,slug=slug,master=request.user); obj=get_object_or_404(SessionRecord,pk=pk,campaign=c); form=PublicationForm(request.POST or None,initial={'confirm':True})
 if request.method=='POST' and form.is_valid(): obj=unpublish_session_record(user=request.user,campaign=c,record=obj) if obj.is_published else publish_session_record(user=request.user,campaign=c,record=obj); return render(request,'history/partials/status.html',{'record':obj,'campaign':c})
 return render(request,'history/partials/publication_form.html',{'form':form,'record':obj,'campaign':c})
@login_required
def protected_media(request,pk,kind):
 obj=get_object_or_404(allowed(request.user),pk=pk); f=obj.audio_file if kind=='audio' else obj.cover_image
 if not f: raise Http404
 return protected_file_response(f,attachment=kind=='audio')
