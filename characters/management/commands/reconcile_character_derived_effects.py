from django.core.management.base import BaseCommand
from django.db import transaction

from characters.models import Character, CharacterDerivedEffect, CharacterFeature, CombatStyle, RULESET_PLAYER_BOOK_1_5_7


class Command(BaseCommand):
    help = 'Reconcilia efeitos calculáveis de features sem alterar nada por padrão.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Persiste os efeitos encontrados.')

    def handle(self, *args, **options):
        apply = options['apply']
        rows = []
        for character in Character.objects.prefetch_related('features', 'derived_effects').order_by('pk'):
            style = CombatStyle.objects.filter(name=character.combat_style, ruleset_version=RULESET_PLAYER_BOOK_1_5_7).first()
            primary = (style.primary_attributes or ['dexterity'])[0] if style else 'dexterity'
            for feature in character.features.filter(is_available=True):
                effect = None
                if feature.name == 'Defesa Ofensiva' and style and len(style.primary_attributes or []) == 1:
                    effect = {
                        'effect_type': CharacterDerivedEffect.EffectType.CR_FORMULA,
                        'formula': 'defesa_ofensiva',
                        'parameters': {'primary_attribute': primary},
                        'source': f'{feature.name}: fórmula estruturada',
                    }
                elif feature.name == 'Defesa Ofensiva':
                    self.stdout.write(f'PENDENTE: personagem={character.pk} {character.name}; Defesa Ofensiva exige o atributo primário escolhido pelo jogador.')
                elif feature.name == 'Defesa Aprimorada':
                    effect = {
                        'effect_type': CharacterDerivedEffect.EffectType.CR_FORMULA,
                        'formula': 'defesa_aprimorada',
                        'parameters': {'primary_attribute': primary},
                        'source': f'{feature.name}: fórmula estruturada',
                    }
                elif feature.name == 'Armadura de Músculos':
                    effect = {
                        'effect_type': CharacterDerivedEffect.EffectType.CR_FORMULA,
                        'formula': 'strength',
                        'parameters': {'primary_attribute': 'strength'},
                        'source': f'{feature.name}: fórmula estruturada',
                    }
                elif feature.name == 'Robusto':
                    effect = {
                        'effect_type': CharacterDerivedEffect.EffectType.HP_PER_LEVEL,
                        'value': 3,
                        'applied_through_level': character.level,
                        'source': f'{feature.name}: +3 PV por nível posterior',
                    }
                if effect:
                    rows.append((character, feature, effect))

        for character, feature, effect in rows:
            prefix = 'APLICARIA' if apply else 'SIMULAÇÃO'
            self.stdout.write(
                f'{prefix}: personagem={character.pk} {character.name}; '
                f'feature={feature.name}; efeito={effect["effect_type"]}; '
                f'parâmetros={effect.get("parameters", {})}'
            )
        if not apply:
            self.stdout.write(f'{len(rows)} efeito(s) encontrado(s). Use --apply para persistir.')
            return
        with transaction.atomic():
            for character, feature, effect in rows:
                CharacterDerivedEffect.objects.update_or_create(
                    character=character,
                    feature=feature,
                    effect_type=effect['effect_type'],
                    defaults=effect,
                )
        self.stdout.write(self.style.SUCCESS(f'{len(rows)} efeito(s) reconciliado(s).'))
