from django import forms
from .models import COMBAT_MODES, COMBAT_RESULTS, NARRATIVE_STATES

class StartCombatForm(forms.Form):
    mode=forms.ChoiceField(label="Modo", choices=COMBAT_MODES, initial="free")
    track_player_resources=forms.BooleanField(label="Controlar recursos dos jogadores", required=False)
class DamageForm(forms.Form):
    raw_damage=forms.IntegerField(label="Dano recebido", min_value=0, required=False)
    reduction=forms.IntegerField(label="Redução", min_value=0, required=False, initial=0)
    final_damage=forms.IntegerField(label="Dano final", min_value=0, required=False)
    mark_defeated_at_zero=forms.BooleanField(label="Marcar derrotado ao chegar a zero", required=False, initial=True)
    def clean(self):
        data=super().clean()
        if data.get("raw_damage") is None and data.get("final_damage") is None: raise forms.ValidationError("Informe o dano recebido ou o dano final.")
        if data.get("reduction") is None: data["reduction"]=0
        return data
class HealForm(forms.Form): amount=forms.IntegerField(label="Cura", min_value=1)
class StateForm(forms.Form):
    state=forms.ChoiceField(label="Estado", choices=NARRATIVE_STATES)
    custom_text=forms.CharField(label="Texto especial", max_length=80, required=False)
    def clean(self):
        d=super().clean()
        if d.get("state") == "special" and not d.get("custom_text"): self.add_error("custom_text", "Descreva o estado especial.")
        return d
class NoteForm(forms.Form): note=forms.CharField(label="Nota", required=False, widget=forms.Textarea(attrs={"rows":3}))
class ModeForm(forms.Form): mode=forms.ChoiceField(label="Modo", choices=COMBAT_MODES)
class OrderForm(forms.Form): order=forms.CharField(label="IDs na ordem")
class FinishCombatForm(forms.Form):
    result=forms.ChoiceField(label="Resultado", choices=[("", "—")]+COMBAT_RESULTS, required=False)
    final_note=forms.CharField(label="Nota final", required=False, widget=forms.Textarea(attrs={"rows":3}))
