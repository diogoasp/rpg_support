from django import forms
from .character_calculation_service import ATTRIBUTE_KEYS, STANDARD_ARRAY
from .creation_catalog_service import allowed_background_skills, allowed_profession_skills, allowed_style_skills
from .models import Background, Character, CharacterCondition, CharacterCreation, CombatStyle, Profession, Skill, Species, SpeciesVariant

class CharacterForm(forms.ModelForm):
    class Meta:
        model=Character; exclude=('campaign','user','created_at','updated_at')
class ResourceForm(forms.Form):
    value=forms.IntegerField(min_value=0,label='Novo valor')
class ConditionForm(forms.ModelForm):
    class Meta: model=CharacterCondition; fields=('name','description')

class CharacterCreationConceptForm(forms.ModelForm):
    class Meta:
        model=CharacterCreation
        fields=("name","concept")
        widgets={"concept":forms.Textarea(attrs={"rows":3})}

class CharacterCreationSpeciesForm(forms.ModelForm):
    class Meta:
        model=CharacterCreation
        fields=("species","species_variant","ancestry_text")
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields["species"].queryset=Species.objects.filter(is_active=True)
        species=self.instance.species if self.instance and self.instance.pk else None
        self.fields["species_variant"].queryset=SpeciesVariant.objects.filter(species=species,is_active=True) if species else SpeciesVariant.objects.none()
        self.fields["species_variant"].required=False
        self.fields["ancestry_text"].required=False

class CharacterCreationStyleForm(forms.ModelForm):
    style_skills=forms.ModelMultipleChoiceField(queryset=Skill.objects.none(),required=False,widget=forms.CheckboxSelectMultiple)
    class Meta:
        model=CharacterCreation
        fields=("combat_style","style_skills","favorite_weapon","innate_ability")
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields["combat_style"].queryset=CombatStyle.objects.filter(is_active=True)
        style=self.instance.combat_style if self.instance and self.instance.pk else None
        self.fields["style_skills"].queryset=allowed_style_skills(style)
        self.fields["favorite_weapon"]=forms.ChoiceField(choices=[("", "---------")]+[(x,x) for x in (style.favorite_weapon_options if style else [])],required=False)
        self.fields["innate_ability"]=forms.ChoiceField(choices=[("", "---------")]+[(x,x) for x in (style.innate_ability_options if style else [])],required=False)

class CharacterCreationProfessionForm(forms.ModelForm):
    profession_skills=forms.ModelMultipleChoiceField(queryset=Skill.objects.none(),required=False,widget=forms.CheckboxSelectMultiple)
    free_skills=forms.ModelMultipleChoiceField(queryset=Skill.objects.none(),required=False,widget=forms.CheckboxSelectMultiple)
    class Meta:
        model=CharacterCreation
        fields=("profession","subprofession","profession_skills","free_skills")
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields["profession"].queryset=Profession.objects.filter(is_active=True,parent__isnull=True)
        profession=self.instance.profession if self.instance and self.instance.pk else None
        self.fields["profession_skills"].queryset=allowed_profession_skills(profession)
        self.fields["free_skills"].queryset=allowed_profession_skills(profession)
        self.fields["subprofession"].queryset=profession.subprofessions.filter(is_active=True) if profession else Profession.objects.none()
        self.fields["subprofession"].required=False

class CharacterCreationAttributesForm(forms.ModelForm):
    for key in ATTRIBUTE_KEYS:
        locals()[f"base_{key}"]=forms.ChoiceField(choices=[("", "---------")]+[(v,v) for v in STANDARD_ARRAY],required=True)
        locals()[f"species_bonus_{key}"]=forms.IntegerField(min_value=0,max_value=2,required=False,initial=0)
        locals()[f"background_bonus_{key}"]=forms.IntegerField(min_value=0,max_value=2,required=False,initial=0)
    class Meta:
        model=CharacterCreation
        fields=("attribute_method",)
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        bases=self.instance.attribute_bases or {}
        species=self.instance.species_attribute_bonuses or {}
        background=self.instance.background_attribute_bonuses or {}
        for key in ATTRIBUTE_KEYS:
            self.fields[f"base_{key}"].initial=bases.get(key)
            self.fields[f"species_bonus_{key}"].initial=species.get(key,0)
            self.fields[f"background_bonus_{key}"].initial=background.get(key,0)
    def save(self,commit=True):
        instance=super().save(commit=False)
        instance.attribute_bases={key:int(self.cleaned_data[f"base_{key}"]) for key in ATTRIBUTE_KEYS}
        instance.species_attribute_bonuses={key:int(self.cleaned_data.get(f"species_bonus_{key}") or 0) for key in ATTRIBUTE_KEYS if int(self.cleaned_data.get(f"species_bonus_{key}") or 0)}
        instance.background_attribute_bonuses={key:int(self.cleaned_data.get(f"background_bonus_{key}") or 0) for key in ATTRIBUTE_KEYS if int(self.cleaned_data.get(f"background_bonus_{key}") or 0)}
        if commit: instance.save()
        return instance

class CharacterCreationBackgroundForm(forms.ModelForm):
    background_skills=forms.ModelMultipleChoiceField(queryset=Skill.objects.none(),required=False,widget=forms.CheckboxSelectMultiple)
    class Meta:
        model=CharacterCreation
        fields=("background","background_skills")
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields["background"].queryset=Background.objects.filter(is_active=True)
        self.fields["background_skills"].queryset=allowed_background_skills(self.instance.background if self.instance and self.instance.pk else None)

class CharacterCreationPersonalityForm(forms.ModelForm):
    class Meta:
        model=CharacterCreation
        fields=("appearance","personality","dream")
        widgets={
            "appearance": forms.Textarea(attrs={"rows":3}),
            "personality": forms.Textarea(attrs={"rows":3}),
            "dream": forms.Textarea(attrs={"rows":3}),
        }

class CharacterCreationEquipmentForm(forms.ModelForm):
    class Meta:
        model=CharacterCreation
        fields=("equipment_choice",)
