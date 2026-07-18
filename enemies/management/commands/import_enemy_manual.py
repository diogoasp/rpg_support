from django.core.management.base import BaseCommand
from django.db import transaction

from enemies.models import Enemy, EnemyAction, EnemyFaction, EnemyFeature
from enemies.seeds.op_enemy_manual import ENEMIES, FACTIONS


class Command(BaseCommand):
    help = "Importa o catálogo global do OP RPG - Manual dos Inimigos - Playtest."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostra o que seria importado sem gravar no banco.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        created = 0
        updated = 0

        with transaction.atomic():
            factions = {}
            for slug, data in FACTIONS.items():
                faction, _ = EnemyFaction.objects.update_or_create(slug=slug, defaults=data)
                factions[slug] = faction

            for data in ENEMIES:
                actions = data["actions"]
                features = data["features"]
                faction = factions[data["faction_slug"]]
                defaults = {
                    key: value
                    for key, value in data.items()
                    if key not in {"slug", "faction_slug", "actions", "features", "experience"}
                }
                defaults["faction"] = faction
                enemy, was_created = Enemy.objects.update_or_create(
                    slug=data["slug"],
                    defaults=defaults,
                )
                created += int(was_created)
                updated += int(not was_created)

                EnemyAction.objects.filter(enemy=enemy).delete()
                EnemyFeature.objects.filter(enemy=enemy).delete()
                EnemyAction.objects.bulk_create(
                    EnemyAction(enemy=enemy, **action) for action in actions
                )
                EnemyFeature.objects.bulk_create(
                    EnemyFeature(enemy=enemy, **feature) for feature in features
                )

            if dry_run:
                transaction.set_rollback(True)

        suffix = " (dry-run, nada gravado)" if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"Manual dos Inimigos importado: {created} criados, {updated} atualizados{suffix}."
            )
        )
