from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from characters.models import Character, CharacterRecordSource


class Command(BaseCommand):
    help = "Registra a SMILE quase perfeita na ficha de M.D. Chefe."

    def add_arguments(self, parser):
        parser.add_argument("character_id", type=int)

    @transaction.atomic
    def handle(self, *args, **options):
        character = Character.objects.select_for_update().filter(
            pk=options["character_id"], name="M.D. Chefe",
            combat_style="Carateca Homem-Peixe",
        ).first()
        if character is None:
            raise CommandError("O ID informado não corresponde à ficha de M.D. Chefe.")

        if character.animal_hp is None:
            character.animal_hp = character.animal_max_hp
            character.save(update_fields=("animal_hp", "updated_at"))

        character.features.get_or_create(
            name="Forma animal",
            source="SMILE quase perfeita",
            defaults={
                "source_type": CharacterRecordSource.MASTER,
                "description": (
                    "O personagem tem forma híbrida permanente e pode assumir a forma animal completa "
                    "como ação bônus por 0 PP. Os PV animais correspondem a 80% dos PV máximos e são "
                    "restaurados no descanso longo. A cada passagem de nível, ganha um Dado de Vida "
                    "adicional e soma o valor médio desse dado aos PV máximos. "
                    "A SMILE não concede forma humana completa, híbrida poderosa ou despertar."
                ),
            },
        )
        self.stdout.write(self.style.SUCCESS("SMILE registrada na ficha de M.D. Chefe."))
