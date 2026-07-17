from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Prefetch
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView, UpdateView
from campaigns.mixins import MasterRequiredMixin, PlayerRequiredMixin
from .forms import CharacterForm, ConditionForm, ResourceForm
from .models import Character, CharacterCondition, CharacterFeature, CharacterTechnique
from .services import add_character_condition, deactivate_character_condition, update_character_resources

def rich_queryset():
    return Character.objects.select_related('campaign','user').prefetch_related(Prefetch('conditions',queryset=CharacterCondition.objects.filter(is_active=True)),Prefetch('techniques',queryset=CharacterTechnique.objects.order_by('sort_order')),Prefetch('features',queryset=CharacterFeature.objects.filter(is_available=True)), 'skills__skill', Prefetch('inventory_items',queryset=__import__('inventory.models',fromlist=['InventoryItem']).InventoryItem.objects.filter(is_active=True,is_visible=True)))
def own_character(request): return get_object_or_404(rich_queryset(),user=request.user,campaign__players=request.user)
def master_character(request,pk): return get_object_or_404(rich_queryset(),pk=pk,campaign__master=request.user)
class PlayerCharacterView(PlayerRequiredMixin,TemplateView):
    template_name='characters/dashboard.html'
    def get_context_data(self,**kw): c=super().get_context_data(**kw); c['character']=own_character(self.request); return c
class CharacterSheetView(PlayerCharacterView): template_name='characters/sheet.html'
class CharacterPrintView(PlayerCharacterView): template_name='characters/print.html'
class MasterCharacterListView(MasterRequiredMixin,TemplateView):
    template_name='characters/master_list.html'
    def get_context_data(self,**kw): c=super().get_context_data(**kw); c['characters']=rich_queryset().filter(campaign__master=self.request.user); return c
class MasterCharacterDetailView(MasterRequiredMixin,TemplateView):
    template_name='characters/master_detail.html'
    def get_context_data(self,**kw): c=super().get_context_data(**kw); c['character']=master_character(self.request,self.kwargs['pk']); return c
class MasterCharacterUpdateView(MasterRequiredMixin,UpdateView):
    model=Character; form_class=CharacterForm; template_name='characters/form.html'
    def get_queryset(self): return Character.objects.filter(campaign__master=self.request.user)
    def get_success_url(self): return f'/mestre/personagens/{self.object.pk}/'
class ResourceUpdateView(MasterRequiredMixin,View):
    resource='hp'
    def post(self,request,pk):
        character=master_character(request,pk); form=ResourceForm(request.POST)
        if form.is_valid():
            try: character=update_character_resources(actor=request.user,character=character,**({self.resource:form.cleaned_data['value']})); form=ResourceForm()
            except ValidationError as e: form.add_error('value',e)
        return render(request,'characters/partials/resource_card.html',{'character':character,'form':form})
class ConditionAddView(MasterRequiredMixin,View):
    def get(self,r,pk): return render(r,'characters/partials/condition_form.html',{'form':ConditionForm(),'character':master_character(r,pk)})
    def post(self,r,pk):
        ch=master_character(r,pk); form=ConditionForm(r.POST)
        if form.is_valid(): add_character_condition(actor=r.user,character=ch,**form.cleaned_data); return render(r,'characters/partials/condition_list.html',{'character':master_character(r,pk)})
        return render(r,'characters/partials/condition_form.html',{'form':form,'character':ch},status=422)
class ConditionDeactivateView(MasterRequiredMixin,View):
    def post(self,r,pk):
        cond=get_object_or_404(CharacterCondition.objects.select_related('character__campaign'),pk=pk,character__campaign__master=r.user); deactivate_character_condition(actor=r.user,condition=cond); return render(r,'characters/partials/condition_list.html',{'character':master_character(r,cond.character_id)})
