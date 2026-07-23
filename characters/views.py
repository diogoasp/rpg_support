from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Prefetch
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import FormView, TemplateView, UpdateView
from campaigns.mixins import MasterRequiredMixin, PlayerRequiredMixin
from campaigns.models import Campaign
from ships.models import Ship
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
    CharacterHpActionForm,
    CharacterForm,
    ConditionForm,
    LevelUpAuthorizationForm,
    LevelUpDraftForm,
    PlayerCharacterSheetForm,
    ResourceForm,
)
from .level_up_service import (
    authorize_level_up,
    available_basic_abilities,
    cancel_level_up_authorization,
    complete_level_up,
    get_level_up_requirements,
    preview_level_up,
    save_level_up_draft,
    start_level_up,
)
from .models import Character, CharacterCondition, CharacterCreation, CharacterFeature, CharacterLevelUp, CharacterLevelUpAuthorization, CharacterLevelUpHistory, CharacterProficiency, CharacterRuleException, CharacterTechnique, CharacterWeapon, Species
from .print_sheet_service import print_sheet_context
from .services import add_character_condition, damage_character, deactivate_character_condition, heal_character, update_character_resources

def rich_queryset():
    return Character.objects.select_related('campaign','user').prefetch_related(Prefetch('conditions',queryset=CharacterCondition.objects.filter(is_active=True)),Prefetch('techniques',queryset=CharacterTechnique.objects.order_by('sort_order')),Prefetch('weapons',queryset=CharacterWeapon.objects.filter(is_available=True).order_by('sort_order','name')),Prefetch('features',queryset=CharacterFeature.objects.filter(is_available=True)),Prefetch('level_up_authorizations',queryset=CharacterLevelUpAuthorization.objects.filter(status__in=(CharacterLevelUpAuthorization.Status.PENDING,CharacterLevelUpAuthorization.Status.IN_PROGRESS)).order_by('-created_at'),to_attr='active_level_up_authorizations'),Prefetch('level_up_history',queryset=CharacterLevelUpHistory.objects.order_by('-created_at'),to_attr='recent_level_up_history'), 'skills__skill', Prefetch('rule_proficiencies',queryset=CharacterProficiency.objects.select_related('proficiency')), Prefetch('inventory_items',queryset=__import__('inventory.models',fromlist=['InventoryItem']).InventoryItem.objects.filter(is_active=True,is_visible=True)))
def own_character(request,slug=None):
    q=rich_queryset().filter(user=request.user,campaign__players=request.user)
    if slug:q=q.filter(campaign__slug=slug)
    return get_object_or_404(q)
def accessible_character(request,slug=None,pk=None):
    if not request.user.is_authenticated:
        raise PermissionDenied
    if request.user.is_master:
        q=rich_queryset().filter(campaign__master=request.user)
        if pk is None:
            raise Http404
    elif request.user.is_player:
        q=rich_queryset().filter(user=request.user,campaign__players=request.user)
        if pk is not None:
            raise Http404
    else:
        raise PermissionDenied
    if pk:q=q.filter(pk=pk)
    if slug:q=q.filter(campaign__slug=slug)
    return get_object_or_404(q)
def master_character(request,pk): return get_object_or_404(rich_queryset(),pk=pk,campaign__master=request.user)
def master_character_card(request,character):
    return render(request,'characters/partials/master_dashboard_card.html',{'character':character})
def htmx_close_modal(response):
    response['HX-Trigger']='modal:close'
    return response
def htmx_modal_validation_response(response):
    response['HX-Retarget']='#modal-content'
    response['HX-Reswap']='innerHTML'
    return response
def split_character_features(character):
    positive_features=[]
    limitation_features=[]
    for feature in character.features.all():
        if feature.source == 'Defeito':
            limitation_features.append(feature)
        else:
            positive_features.append(feature)
    return positive_features, limitation_features
class PlayerCharacterEntryView(PlayerRequiredMixin,View):
    template_name='characters/player_list.html'
    def get(self,request):
        campaigns=request.user.campaigns.select_related('master').prefetch_related(
            Prefetch('characters',Character.objects.filter(user=request.user),to_attr='player_characters'),
            Prefetch('character_creations',CharacterCreation.objects.filter(user=request.user,status__in=(CharacterCreation.Status.DRAFT,CharacterCreation.Status.READY,CharacterCreation.Status.REOPENED)),to_attr='player_character_creations'),
        )
        for campaign in campaigns:
            for creation in getattr(campaign,'player_character_creations',[]):
                creation.current_step_label=CREATION_STEP_LABELS.get(creation.current_step,creation.current_step)
        return render(request,self.template_name,{'campaigns':campaigns})
class PlayerCharacterView(PlayerRequiredMixin,TemplateView):
    template_name='characters/dashboard.html'
    def get_context_data(self,**kw):
        c=super().get_context_data(**kw)
        character=own_character(self.request,self.kwargs.get('slug'))
        c['character']=character
        c['campaign']=character.campaign
        c['ship']=Ship.objects.filter(campaign=character.campaign,is_active=True,belongs_to_crew=True).first()
        c['level_up_authorization']=next(iter(getattr(character,'active_level_up_authorizations',[])),None)
        c['last_level_up']=next(iter(getattr(character,'recent_level_up_history',[])),None)
        return c
class CharacterSheetView(LoginRequiredMixin,TemplateView):
    template_name='characters/sheet.html'
    def get_context_data(self,**kw):
        c=super().get_context_data(**kw)
        character=kw.get('character') or accessible_character(self.request,self.kwargs.get('slug'),self.kwargs.get('pk'))
        c['character']=character
        c['campaign']=character.campaign
        c['ship']=Ship.objects.filter(campaign=character.campaign,is_active=True,belongs_to_crew=True).first()
        c['is_master_viewer']=self.request.user.is_master
        c['can_edit_sheet']=self.request.user.is_player and character.user_id == self.request.user.pk
        c['carrying_capacity']=character.strength*10
        c['featured_item']=next(iter(character.inventory_items.all()),None)
        c['featured_techniques']=[tech for tech in character.techniques.all() if tech.is_featured]
        c['positive_features'],c['limitation_features']=split_character_features(character)
        c['sheet_form']=kw.get('sheet_form') or PlayerCharacterSheetForm(instance=character)
        c['level_up_authorization']=next(iter(getattr(character,'active_level_up_authorizations',[])),None)
        c['last_level_up']=next(iter(getattr(character,'recent_level_up_history',[])),None)
        return c
    def post(self,request,*args,**kwargs):
        character=own_character(request,self.kwargs.get('slug'))
        form=PlayerCharacterSheetForm(request.POST,request.FILES,instance=character)
        if form.is_valid():
            form.save()
            messages.success(request,'Ficha narrativa atualizada.')
            return redirect('characters:sheet',slug=character.campaign.slug)
        return self.render_to_response(self.get_context_data(sheet_form=form,character=character),status=422)

class CharacterPrintView(CharacterSheetView):
    template_name='characters/print.html'
    def get_context_data(self,**kw):
        c=super().get_context_data(**kw)
        c.update(print_sheet_context(c['character']))
        return c
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
    def context(self,creation,form=None,step=None,refresh_validation=True):
        step=step or self.step(creation)
        form=form or (CREATION_FORMS.get(step,CharacterCreationConceptForm))(instance=creation)
        if refresh_validation:
            update_validation_state(creation)
        step_items=[{'key':key,'label':CREATION_STEP_LABELS[key]} for key in CharacterCreation.STEPS]
        species_variant_options={}
        if step=='species':
            species_variant_options={
                str(species.pk): [{'id': variant.pk, 'name': variant.name} for variant in species.variants.filter(is_active=True)]
                for species in Species.objects.filter(is_active=True).prefetch_related('variants')
            }
        return {'campaign':self.campaign,'creation':creation,'form':form,'step':step,'steps':CharacterCreation.STEPS,'step_items':step_items,'options':adaptive_options(creation),'preview':preview_derived_values(creation),'species_variant_options':species_variant_options}
    def invalid_status(self):
        return 200 if self.request.headers.get('HX-Request') else 422
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
                messages.success(request,'Ficha confirmada. O personagem foi criado.')
                return redirect('characters:dashboard',slug=self.campaign.slug)
            except ValidationError as exc:
                errors=getattr(exc,'message_dict',None) or {'confirmação':exc.messages}
                creation.validation_errors=errors
                creation.pending_choices=errors.get('pending_choices',[])
                creation.save(update_fields=('validation_errors','pending_choices','updated_at'))
                messages.error(request,'Não foi possível confirmar a ficha. Resolva as pendências destacadas abaixo.')
                return render(request,self.template_name,self.context(creation,step='review',refresh_validation=False),status=self.invalid_status())
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
        return render(request,self.template_name,self.context(creation,form=form,step=step),status=self.invalid_status())

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
    def get_context_data(self,**kw):
        c=super().get_context_data(**kw)
        character=master_character(self.request,self.kwargs['pk'])
        c['character']=character
        c['level_up_authorization']=next(iter(getattr(character,'active_level_up_authorizations',[])),None)
        c['last_level_up']=next(iter(getattr(character,'recent_level_up_history',[])),None)
        return c
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
class CharacterDamageView(MasterRequiredMixin,View):
    def get(self,request,pk):
        return render(request,'characters/partials/hp_action_form.html',{'form':CharacterHpActionForm(),'character':master_character(request,pk),'action':'damage','title':'Causar dano'})
    def post(self,request,pk):
        character=master_character(request,pk); form=CharacterHpActionForm(request.POST)
        if form.is_valid():
            try: character=damage_character(actor=request.user,character=character,amount=form.cleaned_data['amount'])
            except ValidationError as e: form.add_error('amount',e)
        if form.errors:
            return htmx_modal_validation_response(render(request,'characters/partials/hp_action_form.html',{'form':form,'character':character,'action':'damage','title':'Causar dano'},status=422))
        return htmx_close_modal(master_character_card(request,master_character(request,pk)))
class CharacterHealView(MasterRequiredMixin,View):
    def get(self,request,pk):
        return render(request,'characters/partials/hp_action_form.html',{'form':CharacterHpActionForm(),'character':master_character(request,pk),'action':'heal','title':'Curar'})
    def post(self,request,pk):
        character=master_character(request,pk); form=CharacterHpActionForm(request.POST)
        if form.is_valid():
            try: character=heal_character(actor=request.user,character=character,amount=form.cleaned_data['amount'])
            except ValidationError as e: form.add_error('amount',e)
        if form.errors:
            return htmx_modal_validation_response(render(request,'characters/partials/hp_action_form.html',{'form':form,'character':character,'action':'heal','title':'Curar'},status=422))
        return htmx_close_modal(master_character_card(request,master_character(request,pk)))
class ConditionAddView(MasterRequiredMixin,View):
    def get(self,r,pk): return render(r,'characters/partials/condition_form.html',{'form':ConditionForm(),'character':master_character(r,pk)})
    def post(self,r,pk):
        ch=master_character(r,pk); form=ConditionForm(r.POST)
        if form.is_valid(): add_character_condition(actor=r.user,character=ch,**form.cleaned_data); return render(r,'characters/partials/condition_list.html',{'character':master_character(r,pk)})
        return render(r,'characters/partials/condition_form.html',{'form':form,'character':ch},status=422)
class ConditionDeactivateView(MasterRequiredMixin,View):
    def post(self,r,pk):
        cond=get_object_or_404(CharacterCondition.objects.select_related('character__campaign'),pk=pk,character__campaign__master=r.user); deactivate_character_condition(actor=r.user,condition=cond); return render(r,'characters/partials/condition_list.html',{'character':master_character(r,cond.character_id)})

class MasterLevelUpAuthorizeView(MasterRequiredMixin,View):
    template_name='characters/level_up/authorize.html'
    def get(self,request,pk):
        character=master_character(request,pk)
        form=LevelUpAuthorizationForm()
        try:
            requirements=get_level_up_requirements(character)
        except ValidationError as exc:
            messages.error(request,exc.messages[0] if hasattr(exc,'messages') else str(exc))
            return redirect('characters:master_detail',pk=character.pk)
        return render(request,self.template_name,{'character':character,'form':form,'requirements':requirements,'multi_style_warning':'Multiestilo não está disponível nesta implementação.'})
    def post(self,request,pk):
        character=master_character(request,pk)
        form=LevelUpAuthorizationForm(request.POST)
        if form.is_valid():
            try:
                authorization=authorize_level_up(request.user,character,form.cleaned_data['master_note'])
                messages.success(request,f'Passagem para o {authorization.to_level}º nível autorizada.')
                return redirect('characters:master_detail',pk=character.pk)
            except (ValidationError,PermissionDenied) as exc:
                form.add_error(None,exc.messages[0] if hasattr(exc,'messages') else str(exc))
        requirements=get_level_up_requirements(character)
        return render(request,self.template_name,{'character':character,'form':form,'requirements':requirements,'multi_style_warning':'Multiestilo não está disponível nesta implementação.'},status=422)

class MasterLevelUpCancelView(MasterRequiredMixin,View):
    def post(self,request,pk):
        authorization=get_object_or_404(CharacterLevelUpAuthorization.objects.select_related('character__campaign'),pk=pk,character__campaign__master=request.user)
        try:
            cancel_level_up_authorization(request.user,authorization)
            messages.success(request,'Autorização de passagem de nível cancelada.')
        except ValidationError as exc:
            messages.error(request,exc.messages[0])
        return redirect('characters:master_detail',pk=authorization.character_id)

class PlayerLevelUpWizardView(PlayerRequiredMixin,View):
    template_name='characters/level_up/wizard.html'
    def _authorization(self,request,slug):
        character=own_character(request,slug)
        return get_object_or_404(CharacterLevelUpAuthorization.objects.select_related('character__campaign').filter(character=character,status__in=(CharacterLevelUpAuthorization.Status.PENDING,CharacterLevelUpAuthorization.Status.IN_PROGRESS)))
    def _context(self,request,authorization,process,form=None,preview=None):
        requirements=get_level_up_requirements(process.character)
        form=form or LevelUpDraftForm(character=process.character,requirements=requirements,available_basic_abilities=available_basic_abilities(process.character,process.to_level))
        preview=preview or preview_level_up(process)
        ava_fields=[form[f'ava_{key}'] for key in ('strength','dexterity','constitution','wisdom','willpower','presence')]
        return {'authorization':authorization,'process':process,'character':process.character,'campaign':process.character.campaign,'requirements':requirements,'form':form,'ava_fields':ava_fields,'preview':preview}
    def get(self,request,slug):
        authorization=self._authorization(request,slug)
        try:
            process=start_level_up(request.user,authorization)
        except (ValidationError,PermissionDenied) as exc:
            messages.error(request,exc.messages[0] if hasattr(exc,'messages') else str(exc))
            return redirect('characters:dashboard',slug=slug)
        return render(request,self.template_name,self._context(request,authorization,process))
    def post(self,request,slug):
        authorization=self._authorization(request,slug)
        process=start_level_up(request.user,authorization)
        requirements=get_level_up_requirements(process.character)
        form=LevelUpDraftForm(request.POST,character=process.character,requirements=requirements,available_basic_abilities=available_basic_abilities(process.character,process.to_level))
        if form.is_valid():
            try:
                process=save_level_up_draft(
                    request.user,
                    process,
                    selected_basic_ability=form.cleaned_data.get('basic_ability'),
                    selected_technique_ids=[obj.pk for obj in form.cleaned_data.get('techniques',[])],
                    selected_attribute_increases=form.selected_attribute_increases(),
                    keep_favorite_weapon=form.cleaned_data.get('keep_favorite_weapon'),
                    selected_favorite_weapon=form.cleaned_data.get('favorite_weapon'),
                )
                if request.POST.get('confirm')=='1':
                    complete_level_up(request.user,process)
                    messages.success(request,f'Personagem atualizado para o nível {process.to_level}.')
                    return redirect('characters:dashboard',slug=slug)
                messages.success(request,'Rascunho da passagem de nível salvo.')
                return redirect('characters:level_up',slug=slug)
            except (ValidationError,PermissionDenied) as exc:
                form.add_error(None,exc.messages[0] if hasattr(exc,'messages') else str(exc))
        return render(request,self.template_name,self._context(request,authorization,process,form=form),status=422)

class PlayerLevelUpPreviewView(PlayerRequiredMixin,View):
    def post(self,request,slug):
        authorization=get_object_or_404(CharacterLevelUpAuthorization.objects.select_related('character__campaign'),character__campaign__slug=slug,character__user=request.user,status__in=(CharacterLevelUpAuthorization.Status.PENDING,CharacterLevelUpAuthorization.Status.IN_PROGRESS))
        process=start_level_up(request.user,authorization)
        requirements=get_level_up_requirements(process.character)
        form=LevelUpDraftForm(request.POST,character=process.character,requirements=requirements,available_basic_abilities=available_basic_abilities(process.character,process.to_level))
        preview=preview_level_up(process)
        if form.is_valid():
            try:
                increments=form.selected_attribute_increases() if requirements['style_level'].grants_attribute_increase else {}
                preview=preview_level_up(process,form.cleaned_data.get('basic_ability'),increments,form.cleaned_data.get('favorite_weapon'),form.cleaned_data.get('keep_favorite_weapon'))
            except ValidationError as exc:
                form.add_error(None,exc.messages[0])
        return render(request,'characters/level_up/partials/preview.html',{'preview':preview,'form':form,'process':process,'requirements':requirements},status=200 if not form.errors else 422)
