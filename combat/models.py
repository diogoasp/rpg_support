from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

COMBAT_STATUS = [("active", "Ativo"), ("paused", "Pausado"), ("finished", "Encerrado"), ("cancelled", "Cancelado")]
COMBAT_MODES = [("free", "Livre"), ("simple_order", "Ordem simples"), ("initiative", "Iniciativa completa")]
COMBAT_RESULTS = [("victory", "Vitória"), ("defeat", "Derrota"), ("escape", "Fuga"), ("negotiation", "Negociação"), ("interrupted", "Interrompido"), ("other", "Outro")]
COMBATANT_TYPES = [("enemy", "Inimigo"), ("player", "Jogador"), ("ally", "Aliado"), ("neutral", "Neutro")]
NARRATIVE_STATES = [("normal", "Normal"), ("wounded", "Ferido"), ("badly_wounded", "Muito ferido"), ("surrendered", "Rendido"), ("fleeing", "Fugindo"), ("unconscious", "Inconsciente"), ("defeated", "Derrotado"), ("special", "Especial")]


class Combat(models.Model):
    encounter = models.ForeignKey("encounters.Encounter", on_delete=models.PROTECT, related_name="combats")
    campaign = models.ForeignKey("campaigns.Campaign", on_delete=models.CASCADE, related_name="combats")
    status = models.CharField(max_length=12, choices=COMBAT_STATUS, default="active", db_index=True)
    mode = models.CharField(max_length=20, choices=COMBAT_MODES, default="free")
    track_player_resources = models.BooleanField(default=False)
    round_number = models.PositiveIntegerField(default=1)
    current_turn_index = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    master_notes = models.TextField(blank=True)
    result = models.CharField(max_length=20, choices=COMBAT_RESULTS, blank=True)
    final_note = models.TextField(blank=True)

    class Meta:
        ordering = ("-updated_at",)
        constraints = [
            models.UniqueConstraint(fields=("encounter",), condition=Q(status="active"), name="one_active_combat_per_encounter"),
            models.UniqueConstraint(fields=("campaign",), condition=Q(status="active"), name="one_active_combat_per_campaign"),
        ]

    def clean(self):
        if self.encounter_id and self.campaign_id and self.encounter.campaign_id != self.campaign_id:
            raise ValidationError({"encounter": "O encontro deve pertencer à campanha."})

    def __str__(self): return f"{self.encounter} — {self.get_status_display()}"


class Combatant(models.Model):
    combat = models.ForeignKey(Combat, on_delete=models.CASCADE, related_name="combatants")
    enemy = models.ForeignKey("enemies.Enemy", on_delete=models.PROTECT, null=True, blank=True, related_name="combatants")
    character = models.ForeignKey("characters.Character", on_delete=models.PROTECT, null=True, blank=True, related_name="combatants")
    combatant_type = models.CharField(max_length=10, choices=COMBATANT_TYPES)
    display_name = models.CharField(max_length=150)
    image = models.ImageField(upload_to="combat/snapshots/", blank=True)
    max_hp = models.PositiveIntegerField(default=1)
    current_hp = models.PositiveIntegerField(default=1)
    max_power_points = models.PositiveIntegerField(default=0)
    current_power_points = models.PositiveIntegerField(default=0)
    armor_class = models.PositiveSmallIntegerField(default=10)
    resistance_bonus = models.SmallIntegerField(default=0)
    initiative = models.SmallIntegerField(null=True, blank=True)
    turn_order = models.PositiveIntegerField(default=0)
    narrative_state = models.CharField(max_length=20, choices=NARRATIVE_STATES, blank=True)
    custom_narrative_state = models.CharField(max_length=80, blank=True)
    is_defeated = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_boss = models.BooleanField(default=False)
    master_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("turn_order", "pk")
        constraints = [models.CheckConstraint(condition=(Q(enemy__isnull=False, character__isnull=True) | Q(enemy__isnull=True, character__isnull=False)), name="combatant_exactly_one_reference"), models.CheckConstraint(condition=Q(current_hp__gte=0) & Q(current_hp__lte=models.F("max_hp")), name="combatant_hp_bounds")]

    def clean(self):
        errors = {}
        if bool(self.enemy_id) == bool(self.character_id): errors["enemy"] = "Informe inimigo ou personagem, exclusivamente."
        if self.current_hp > self.max_hp: errors["current_hp"] = "PV atual não pode exceder o máximo."
        if self.combat_id and self.character_id and self.character.campaign_id != self.combat.campaign_id: errors["character"] = "O personagem deve pertencer à campanha."
        if errors: raise ValidationError(errors)

    @property
    def hp_percentage(self): return round(self.current_hp * 100 / self.max_hp) if self.max_hp else 0

    @property
    def suggested_narrative_state(self):
        if self.current_hp <= 0: return "defeated"
        thresholds = settings.COMBAT_NARRATIVE_HP_THRESHOLDS
        if self.hp_percentage <= thresholds["wounded"]: return "badly_wounded"
        if self.hp_percentage <= thresholds["normal"]: return "wounded"
        return "normal"

    @property
    def effective_narrative_state(self): return self.narrative_state or self.suggested_narrative_state
    @property
    def narrative_state_label(self):
        if self.effective_narrative_state == "special" and self.custom_narrative_state: return self.custom_narrative_state
        return dict(NARRATIVE_STATES).get(self.effective_narrative_state, self.effective_narrative_state)


class HPChange(models.Model):
    combatant = models.ForeignKey(Combatant, on_delete=models.CASCADE, related_name="hp_changes")
    previous_hp = models.PositiveIntegerField()
    new_hp = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_reverted = models.BooleanField(default=False)

    class Meta: ordering = ("-created_at", "-pk")


class CombatNote(models.Model):
    NOTE_TYPES = [("note", "Observação"), ("phase", "Mudança de fase"), ("escape", "Fuga"), ("surrender", "Rendição"), ("reinforcement", "Reforço"), ("objective", "Objetivo")]
    combat = models.ForeignKey(Combat, on_delete=models.CASCADE, related_name="notes")
    combatant = models.ForeignKey(Combatant, on_delete=models.CASCADE, null=True, blank=True, related_name="notes")
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default="note")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
