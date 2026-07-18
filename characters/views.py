from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Prefetch
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import FormView, TemplateView, UpdateView
from campaigns.mixins import MasterRequiredMixin, PlayerRequiredMixin
from campaigns.models import Campaign
from .character_calculation_service import preview_derived_values
from .character_creation_service import confirm_creation, get_or_create_draft, update_validation_state
from .choice_dependency_service import adaptive_options
from .forms import (
    CharacterCreationAttributesForm,
    CharacterCreationBackgroundForm,
    CharacterCreationConceptForm,
    CharacterCreationEquipmentForm,
    CharacterCreationPersonalityForm,
    CharacterCreationProfessionForm,
    CharacterCreationSpeciesForm,
    CharacterCreationStyleForm,
    CharacterForm,
    ConditionForm,
    ResourceForm,
)
from .models import Character, CharacterCondition, CharacterCreation, CharacterFeature, CharacterRuleException, CharacterTechnique
from .services import add_character_condition, deactivate_character_condition, update_character_resources

def rich_queryset():
    return Character.objects.select_related('campaign','user').prefetch_related(Prefetch('conditions',queryset=CharacterCondition.objects.filter(is_active=True)),Prefetch('techniques',queryset=CharacterTechnique.objects.order_by('sort_order')),Prefetch('features',queryset=CharacterFeature.objects.filter(is_available=True)), 'skills__skill', Prefetch('inventory_items',queryset=__import__('inventory.models',fromlist=['InventoryItem']).InventoryItem.objects.filter(is_active=True,is_visible=True)))
def own_character(request,slug=None):
    q=rich_queryset().filter(user=request.user,campaign__players=request.user)
    if slug:q=q.filter(campaign__slug=slug)
    return get_object_or_404(q)
def master_character(request,pk): return get_object_or_404(rich_queryset(),pk=pk,campaign__master=request.user)
class PlayerCharacterEntryView(PlayerRequiredMixin,View):
    def get(self,request): return redirect('dashboard:player')
class PlayerCharacterView(PlayerRequiredMixin,TemplateView):
    template_name='characters/dashboard.html'
    def get_context_data(self,**kw): c=super().get_context_data(**kw); c['character']=own_character(self.request,self.kwargs.get('slug')); return c
class CharacterSheetView(PlayerCharacterView): template_name='characters/sheet.html'
class CharacterPrintView(PlayerCharacterView): template_name='characters/print.html'
CREATION_FORMS={
    'concept':CharacterCreationConceptForm,
    'species':CharacterCreationSpeciesForm,
    'style':CharacterCreationStyleForm,
    'profession':CharacterCreationProfessionForm,
    'attributes':CharacterCreationAttributesForm,
    'background':CharacterCreationBackgroundForm,
    'personality':CharacterCreationPersonalityForm,
    'equipment':CharacterCreationEquipmentForm,
}
CREATION_STEP_LABELS={
    'concept':'Conceito',
    'species':'Espécie',
    'style':'Estilo',
    'profession':'Profissão',
    'attributes':'Atributos',
    'background':'Antecedente',
    'personality':'Personalidade',
    'pending':'Pendências',
    'equipment':'Equipamentos',
    'review':'Revisão',
}

class PlayerCharacterCreateView(PlayerRequiredMixin,View):
    template_name='characters/creation/wizard.html'
    def dispatch(self,request,*args,**kwargs):
        if not request.user.is_authenticated or not request.user.is_player:
            return super().dispatch(request,*args,**kwargs)
        self.campaign=get_object_or_404(Campaign.objects.filter(players=request.user),slug=kwargs['slug'])
        existing=Character.objects.filter(campaign=self.campaign,user=request.user).first()
        if existing:return redirect('characters:dashboard',slug=self.campaign.slug)
        return super().dispatch(request,*args,**kwargs)
    def creation(self): return get_or_create_draft(self.campaign,self.request.user)
    def step(self,creation):
        requested=self.request.GET.get('step') or self.request.POST.get('step') or creation.current_step
        return requested if requested in CharacterCreation.STEPS else 'concept'
    def context(self,creation,form=None,step=None):
        step=step or self.step(creation)
        form=form or (CREATION_FORMS.get(step,CharacterCreationConceptForm))(instance=creation)
        update_validation_state(creation)
        step_items=[{'key':key,'label':CREATION_STEP_LABELS[key]} for key in CharacterCreation.STEPS]
        return {'campaign':self.campaign,'creation':creation,'form':form,'step':step,'steps':CharacterCreation.STEPS,'step_items':step_items,'options':adaptive_options(creation),'preview':preview_derived_values(creation)}
    def get(self,request,*args,**kwargs):
        creation=self.creation(); step=self.step(creation)
        if step in ('pending','review'):
            update_validation_state(creation)
        return render(request,self.template_name,self.context(creation,step=step))
    def post(self,request,*args,**kwargs):
        creation=self.creation(); step=self.step(creation)
        if step=='review' and request.POST.get('confirm')=='1':
            try:
                confirm_creation(creation,actor=request.user)
                return redirect('characters:dashboard',slug=self.campaign.slug)
            except ValidationError:
                return render(request,self.template_name,self.context(creation,step='review'),status=422)
        form_class=CREATION_FORMS.get(step,CharacterCreationConceptForm); form=form_class(request.POST,instance=creation)
        if form.is_valid():
            creation=form.save()
            if step not in creation.completed_steps:
                creation.completed_steps=[*creation.completed_steps,step]
            next_step=request.POST.get('next_step') or _next_step(step)
            creation.current_step=next_step
            creation.save()
            if hasattr(form,'save_m2m'): form.save_m2m()
            update_validation_state(creation)
            return redirect(f"{request.path}?step={next_step}")
        return render(request,self.template_name,self.context(creation,form=form,step=step),status=422)

def _next_step(step):
    try: return CharacterCreation.STEPS[min(CharacterCreation.STEPS.index(step)+1,len(CharacterCreation.STEPS)-1)]
    except ValueError: return 'concept'

class CharacterCreationPreviewView(PlayerRequiredMixin,View):
    def get(self,request,slug):
        campaign=get_object_or_404(Campaign.objects.filter(players=request.user),slug=slug)
        creation=get_or_create_draft(campaign,request.user)
        return render(request,'characters/creation/partials/preview.html',{'creation':creation,'preview':preview_derived_values(creation)})

class CharacterCreationOptionsView(PlayerRequiredMixin,View):
    def get(self,request,slug):
        campaign=get_object_or_404(Campaign.objects.filter(players=request.user),slug=slug)
        creation=get_or_create_draft(campaign,request.user)
        return render(request,'characters/creation/partials/options.html',{'creation':creation,'options':adaptive_options(creation)})
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

class MasterCreationExceptionView(MasterRequiredMixin,View):
    def post(self,request,pk):
        creation=get_object_or_404(CharacterCreation.objects.select_related('campaign'),pk=pk,campaign__master=request.user)
        justification=request.POST.get('justification','').strip()
        ignored_rule=request.POST.get('ignored_rule','Exceção de criação').strip()
        if not justification:
            return HttpResponse('Justificativa obrigatória.',status=422)
        CharacterRuleException.objects.create(creation=creation,user=request.user,ignored_rule=ignored_rule,justification=justification)
        creation.approved_by_master=True; creation.save(update_fields=('approved_by_master','updated_at'))
        return redirect('characters:master_list')

class MasterCreationReopenView(MasterRequiredMixin,View):
    def post(self,request,pk):
        creation=get_object_or_404(CharacterCreation.objects.select_related('campaign'),pk=pk,campaign__master=request.user)
        creation.status=CharacterCreation.Status.REOPENED; creation.completed_at=None; creation.save(update_fields=('status','completed_at','updated_at'))
        return redirect('characters:master_list')
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
