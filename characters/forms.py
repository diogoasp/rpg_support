from django import forms
from .character_calculation_service import ATTRIBUTE_KEYS, ATTRIBUTE_LABELS, POINT_DISTRIBUTION_MAX, POINT_DISTRIBUTION_MIN, POINT_DISTRIBUTION_TOTAL, remaining_attribute_points
from .creation_catalog_service import allowed_background_skills, allowed_profession_skills, allowed_style_skills
from .models import Background, CANONICAL_ATTRIBUTES, Character, CharacterCondition, CharacterCreation, CombatStyle, Profession, Skill, Species, SpeciesVariant, ZoanAncestryTrait

class CharacterForm(forms.ModelForm):
    class Meta:
        model=Character; exclude=('campaign','user','created_at','updated_at')
class PlayerCharacterSheetForm(forms.ModelForm):
    class Meta:
        model=Character
        fields=("portrait","age","height","weight","dream_path","appearance","personality","dream","notes")
        labels={"portrait":"Retrato/ilustração","age":"Idade","height":"Altura","weight":"Peso","dream_path":"Caminho","appearance":"Aparência","personality":"Personalidade","dream":"Sonho","notes":"História e notas"}
        widgets={
            "appearance":forms.Textarea(attrs={"rows":4}),
            "personality":forms.Textarea(attrs={"rows":4}),
            "dream":forms.Textarea(attrs={"rows":4}),
            "notes":forms.Textarea(attrs={"rows":6}),
        }
class ResourceForm(forms.Form):
    value=forms.IntegerField(min_value=0,label='Novo valor')
class CharacterHpActionForm(forms.Form):
    amount=forms.IntegerField(min_value=1,label='Quantidade')
class ConditionForm(forms.ModelForm):
    class Meta: model=CharacterCondition; fields=('name','description')

class CharacterCreationConceptForm(forms.ModelForm):
    class Meta:
        model=CharacterCreation
        fields=("name","concept","age","height","weight","dream_path")
        labels={"name":"Nome","concept":"Conceito","age":"Idade","height":"Altura","weight":"Peso","dream_path":"Caminho"}
        widgets={"concept":forms.Textarea(attrs={"rows":3})}

class CharacterCreationSpeciesForm(forms.ModelForm):
    mixed_species_origins=forms.ModelMultipleChoiceField(label="Origens do mestiço",queryset=Species.objects.none(),required=False,widget=forms.CheckboxSelectMultiple)
    species_bonus_mode=forms.ChoiceField(label="Bônus de atributo da espécie",choices=(("plus2","+2 em um atributo"),("plus1_plus1","+1 em dois atributos diferentes")),required=True)
    species_bonus_primary=forms.ChoiceField(label="Primeiro atributo",required=False)
    species_bonus_secondary=forms.ChoiceField(label="Segundo atributo",required=False)
    common_ancestry_traits=forms.ModelMultipleChoiceField(label="Traços comuns de ancestralidade",queryset=ZoanAncestryTrait.objects.none(),required=False,widget=forms.CheckboxSelectMultiple)
    specific_ancestry_traits=forms.ModelMultipleChoiceField(label="Traços específicos de ancestralidade",queryset=ZoanAncestryTrait.objects.none(),required=False,widget=forms.CheckboxSelectMultiple)
    predator_ancestry=forms.BooleanField(label="Predador",required=False)
    carnivore_hunter=forms.BooleanField(label="Ancestral carnívoro caçador",required=False)
    dial_choice=forms.CharField(label="Dial inicial",required=False,max_length=120)
    expert_skill=forms.ModelChoiceField(label="Perícia com especialização",queryset=Skill.objects.none(),required=False)
    snake_name=forms.CharField(label="Nome da Cobra Bélica",required=False,max_length=120)
    restricted_skill=forms.ChoiceField(label="Perícia especial",choices=(("", "---------"),("Haki","Haki"),("Sobrenatural","Sobrenatural"),("Sorte","Sorte")),required=False)
    marine_ancestry=forms.CharField(label="Ancestralidade marinha",required=False,max_length=150)
    class Meta:
        model=CharacterCreation
        fields=("species","species_variant","mixed_species_origins","ancestry_text")
        labels={"species":"Espécie","species_variant":"Variante","ancestry_text":"Ancestralidade"}
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields["species"].queryset=Species.objects.filter(is_active=True)
        self.fields["mixed_species_origins"].queryset=Species.objects.filter(is_active=True).exclude(slug="mestico")
        species_id=self.data.get("species") if self.is_bound else None
        species=Species.objects.filter(pk=species_id).first() if species_id else (self.instance.species if self.instance and self.instance.pk else None)
        self.fields["species_variant"].queryset=SpeciesVariant.objects.filter(species=species,is_active=True) if species else SpeciesVariant.objects.none()
        self.fields["species_variant"].required=False
        self.fields["ancestry_text"].required=False
        self.fields["common_ancestry_traits"].queryset=ZoanAncestryTrait.objects.filter(is_active=True,trait_type=ZoanAncestryTrait.TraitType.COMMON)
        self.fields["specific_ancestry_traits"].queryset=ZoanAncestryTrait.objects.filter(is_active=True,trait_type=ZoanAncestryTrait.TraitType.SPECIFIC)
        self.fields["expert_skill"].queryset=Skill.objects.filter(is_active=True)
        choices=[("", "---------")]+list(CANONICAL_ATTRIBUTES)
        self.fields["species_bonus_primary"].choices=choices
        self.fields["species_bonus_secondary"].choices=choices
        bonuses=self.instance.species_attribute_bonuses or {}
        ancestry_choices=self.instance.ancestry_choices or {}
        non_zero=[key for key,value in bonuses.items() if int(value)]
        self.fields["species_bonus_mode"].initial="plus2" if any(int(v)==2 for v in bonuses.values()) else "plus1_plus1"
        self.fields["species_bonus_primary"].initial=non_zero[0] if non_zero else ""
        self.fields["species_bonus_secondary"].initial=non_zero[1] if len(non_zero)>1 else ""
        self.fields["common_ancestry_traits"].initial=ZoanAncestryTrait.objects.filter(slug__in=ancestry_choices.get("common_traits",[]))
        self.fields["specific_ancestry_traits"].initial=ZoanAncestryTrait.objects.filter(slug__in=ancestry_choices.get("specific_traits",[]))
        self.fields["predator_ancestry"].initial=bool(ancestry_choices.get("predator"))
        self.fields["carnivore_hunter"].initial=bool(ancestry_choices.get("carnivore_hunter"))
        self.fields["dial_choice"].initial=ancestry_choices.get("dial","")
        self.fields["expert_skill"].initial=Skill.objects.filter(slug=ancestry_choices.get("expert_skill","")).first()
        self.fields["snake_name"].initial=ancestry_choices.get("snake_name","")
        self.fields["restricted_skill"].initial=ancestry_choices.get("restricted_skill","")
        self.fields["marine_ancestry"].initial=ancestry_choices.get("marine_ancestry","")
    def clean(self):
        cleaned=super().clean()
        species=cleaned.get("species")
        variant=cleaned.get("species_variant")
        mode=cleaned.get("species_bonus_mode")
        primary=cleaned.get("species_bonus_primary")
        secondary=cleaned.get("species_bonus_secondary")
        common_traits=cleaned.get("common_ancestry_traits")
        specific_traits=cleaned.get("specific_ancestry_traits")
        if not primary:
            self.add_error("species_bonus_primary","Escolha o atributo do bônus racial.")
        if mode=="plus1_plus1" and (not secondary or secondary==primary):
            self.add_error("species_bonus_secondary","Escolha um segundo atributo diferente.")
        if species and species.slug=="mestico" and len(cleaned.get("mixed_species_origins") or [])!=2:
            self.add_error("mixed_species_origins","Escolha exatamente duas origens para Mestiço.")
        if species and "dial" in species.required_choices and not cleaned.get("dial_choice"):
            self.add_error("dial_choice","Informe o dial inicial.")
        if species and "ancestry" in species.required_choices:
            if not cleaned.get("ancestry_text"):
                self.add_error("ancestry_text","Informe a ancestralidade.")
            has_trait=bool(common_traits or specific_traits or cleaned.get("predator_ancestry"))
            if not has_trait and not (variant and "marine_ancestry" in variant.required_choices):
                self.add_error("common_ancestry_traits","Escolha ao menos um traço de ancestralidade.")
        if common_traits and len(common_traits)>2:
            self.add_error("common_ancestry_traits","Escolha no máximo dois traços comuns.")
        if specific_traits and len(specific_traits)>1:
            self.add_error("specific_ancestry_traits","Escolha no máximo um traço específico.")
        if cleaned.get("predator_ancestry") and (common_traits or specific_traits):
            self.add_error("predator_ancestry","Predador substitui os demais traços de ancestralidade.")
        if cleaned.get("predator_ancestry") and not cleaned.get("carnivore_hunter"):
            self.add_error("carnivore_hunter","Predador exige ancestral carnívoro caçador ou autorização do mestre.")
        if variant:
            required=variant.required_choices or []
            if "expert_skill" in required and not cleaned.get("expert_skill"):
                self.add_error("expert_skill","Escolha a perícia com especialização.")
            if "snake_name" in required and not cleaned.get("snake_name"):
                self.add_error("snake_name","Informe o nome da Cobra Bélica.")
            if "restricted_skill" in required and not cleaned.get("restricted_skill"):
                self.add_error("restricted_skill","Escolha Haki, Sobrenatural ou Sorte.")
            if "marine_ancestry" in required and not cleaned.get("marine_ancestry"):
                self.add_error("marine_ancestry","Informe a ancestralidade marinha.")
        return cleaned
    def save(self,commit=True):
        instance=super().save(commit=False)
        primary=self.cleaned_data.get("species_bonus_primary")
        secondary=self.cleaned_data.get("species_bonus_secondary")
        if self.cleaned_data.get("species_bonus_mode")=="plus2":
            instance.species_attribute_bonuses={primary:2}
        else:
            instance.species_attribute_bonuses={primary:1,secondary:1}
        instance.ancestry_choices={
            "common_traits":[trait.slug for trait in self.cleaned_data.get("common_ancestry_traits",[])],
            "specific_traits":[trait.slug for trait in self.cleaned_data.get("specific_ancestry_traits",[])],
            "predator": self.cleaned_data.get("predator_ancestry") or False,
            "carnivore_hunter": self.cleaned_data.get("carnivore_hunter") or False,
            "dial": self.cleaned_data.get("dial_choice",""),
            "expert_skill": self.cleaned_data["expert_skill"].slug if self.cleaned_data.get("expert_skill") else "",
            "snake_name": self.cleaned_data.get("snake_name",""),
            "restricted_skill": self.cleaned_data.get("restricted_skill",""),
            "marine_ancestry": self.cleaned_data.get("marine_ancestry",""),
        }
        origins=list(self.cleaned_data.get("mixed_species_origins") or [])
        if commit:
            instance.save()
            instance.mixed_species_origins.set(origins)
        return instance

class CharacterCreationStyleForm(forms.ModelForm):
    style_skills=forms.ModelMultipleChoiceField(label="Perícias do estilo",queryset=Skill.objects.none(),required=False,widget=forms.CheckboxSelectMultiple)
    class Meta:
        model=CharacterCreation
        fields=("combat_style","style_skills","favorite_weapon","innate_ability")
        labels={"combat_style":"Estilo de combate","favorite_weapon":"Arma favorita","innate_ability":"Habilidade básica inata"}
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields["combat_style"].queryset=CombatStyle.objects.filter(is_active=True)
        style_id=self.data.get("combat_style") if self.is_bound else None
        style=CombatStyle.objects.filter(pk=style_id).first() if style_id else (self.instance.combat_style if self.instance and self.instance.pk else None)
        self.fields["style_skills"].queryset=allowed_style_skills(style)
        self.fields["favorite_weapon"]=forms.ChoiceField(label="Arma favorita",choices=[("", "---------")]+[(x,x) for x in (style.favorite_weapon_options if style else [])],required=False)
        self.fields["innate_ability"]=forms.ChoiceField(label="Habilidade básica inata",choices=[("", "---------")]+[(x,x) for x in (style.innate_ability_options if style else [])],required=False)

class CharacterCreationProfessionForm(forms.ModelForm):
    profession_skills=forms.ModelMultipleChoiceField(label="Perícias da profissão",queryset=Skill.objects.none(),required=False,widget=forms.CheckboxSelectMultiple)
    free_skills=forms.ModelMultipleChoiceField(label="Perícias livres",queryset=Skill.objects.none(),required=False,widget=forms.CheckboxSelectMultiple)
    class Meta:
        model=CharacterCreation
        fields=("profession","subprofession","profession_skills","free_skills")
        labels={"profession":"Profissão","subprofession":"Subprofissão"}
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields["profession"].queryset=Profession.objects.filter(is_active=True,parent__isnull=True)
        profession_id=self.data.get("profession") if self.is_bound else None
        profession=Profession.objects.filter(pk=profession_id).first() if profession_id else (self.instance.profession if self.instance and self.instance.pk else None)
        self.fields["profession_skills"].queryset=allowed_profession_skills(profession)
        self.fields["free_skills"].queryset=allowed_profession_skills(profession)
        self.fields["subprofession"].queryset=profession.subprofessions.filter(is_active=True) if profession else Profession.objects.none()
        self.fields["subprofession"].required=False

class CharacterCreationAttributesForm(forms.ModelForm):
    for key in ATTRIBUTE_KEYS:
        locals()[f"base_{key}"]=forms.IntegerField(label=ATTRIBUTE_LABELS[key],min_value=POINT_DISTRIBUTION_MIN,max_value=POINT_DISTRIBUTION_MAX,required=True)
    class Meta:
        model=CharacterCreation
        fields=("attribute_method",)
        labels={"attribute_method":"Método de geração"}
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        bases=self.instance.attribute_bases or {}
        for key in ATTRIBUTE_KEYS:
            self.fields[f"base_{key}"].initial=bases.get(key,POINT_DISTRIBUTION_MIN)
            self.fields[f"base_{key}"].help_text=f"{POINT_DISTRIBUTION_MIN} a {POINT_DISTRIBUTION_MAX}"
        self.remaining_points=remaining_attribute_points(bases or {key:POINT_DISTRIBUTION_MIN for key in ATTRIBUTE_KEYS})
    def clean(self):
        cleaned=super().clean()
        values={key:cleaned.get(f"base_{key}") for key in ATTRIBUTE_KEYS}
        if any(value is None for value in values.values()):
            return cleaned
        total=sum(int(value) for value in values.values())
        self.remaining_points=POINT_DISTRIBUTION_TOTAL-total
        if total>POINT_DISTRIBUTION_TOTAL:
            raise forms.ValidationError(f"A soma dos atributos base não pode ultrapassar {POINT_DISTRIBUTION_TOTAL} pontos. Total atual: {total}.")
        return cleaned
    def save(self,commit=True):
        instance=super().save(commit=False)
        instance.attribute_bases={key:int(self.cleaned_data[f"base_{key}"]) for key in ATTRIBUTE_KEYS}
        if commit: instance.save()
        return instance

class CharacterCreationBackgroundForm(forms.ModelForm):
    background_skills=forms.ModelMultipleChoiceField(label="Perícias do antecedente",queryset=Skill.objects.none(),required=False,widget=forms.CheckboxSelectMultiple)
    background_bonus_mode=forms.ChoiceField(label="Bônus de atributo do antecedente",choices=(("plus2","+2 em um atributo"),("plus1_plus1","+1 em dois atributos diferentes")),required=True)
    background_bonus_primary=forms.ChoiceField(label="Primeiro atributo",required=False)
    background_bonus_secondary=forms.ChoiceField(label="Segundo atributo",required=False)
    class Meta:
        model=CharacterCreation
        fields=("background","background_skills")
        labels={"background":"Antecedente"}
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields["background"].queryset=Background.objects.filter(is_active=True)
        background_id=self.data.get("background") if self.is_bound else None
        background=Background.objects.filter(pk=background_id).first() if background_id else (self.instance.background if self.instance and self.instance.pk else None)
        self.fields["background_skills"].queryset=allowed_background_skills(background)
        choices=[("", "---------")]+list(CANONICAL_ATTRIBUTES)
        self.fields["background_bonus_primary"].choices=choices
        self.fields["background_bonus_secondary"].choices=choices
        bonuses=self.instance.background_attribute_bonuses or {}
        non_zero=[key for key,value in bonuses.items() if int(value)]
        self.fields["background_bonus_mode"].initial="plus2" if any(int(v)==2 for v in bonuses.values()) else "plus1_plus1"
        self.fields["background_bonus_primary"].initial=non_zero[0] if non_zero else (background.recommended_attribute if background else "")
        self.fields["background_bonus_secondary"].initial=non_zero[1] if len(non_zero)>1 else ""
    def clean(self):
        cleaned=super().clean()
        mode=cleaned.get("background_bonus_mode")
        primary=cleaned.get("background_bonus_primary")
        secondary=cleaned.get("background_bonus_secondary")
        if not primary:
            self.add_error("background_bonus_primary","Escolha o atributo do antecedente.")
        if mode=="plus1_plus1" and (not secondary or secondary==primary):
            self.add_error("background_bonus_secondary","Escolha um segundo atributo diferente.")
        return cleaned
    def save(self,commit=True):
        instance=super().save(commit=False)
        primary=self.cleaned_data.get("background_bonus_primary")
        secondary=self.cleaned_data.get("background_bonus_secondary")
        if self.cleaned_data.get("background_bonus_mode")=="plus2":
            instance.background_attribute_bonuses={primary:2}
        else:
            instance.background_attribute_bonuses={primary:1,secondary:1}
        if commit: instance.save()
        return instance

class CharacterCreationPersonalityForm(forms.ModelForm):
    class Meta:
        model=CharacterCreation
        fields=("appearance","personality","dream")
        labels={"appearance":"Aparência","personality":"Personalidade","dream":"Sonho"}
        widgets={
            "appearance": forms.Textarea(attrs={"rows":3}),
            "personality": forms.Textarea(attrs={"rows":3}),
            "dream": forms.Textarea(attrs={"rows":3}),
        }

class CharacterCreationEquipmentForm(forms.ModelForm):
    class Meta:
        model=CharacterCreation
        fields=("equipment_choice",)
        labels={"equipment_choice":"Escolha de equipamento"}
