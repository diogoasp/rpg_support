from django.core.management import call_command
from django.core.management.base import BaseCommand

from accounts.models import User
from campaigns.models import Campaign
from ships.models import Ship


class Command(BaseCommand):
    help = "Seed idempotente de desenvolvimento com a campanha e o navio reais da mesa."

    def handle(self, *args, **options):
        call_command("seed_skills")

        master, _ = User.objects.update_or_create(
            username="diogo",
            defaults={"role": User.Role.MASTER, "email": "diogo@example.test"},
        )
        if not master.has_usable_password():
            master.set_password("demo-rpg-2026")
            master.save(update_fields=["password"])

        campaign, _ = Campaign.objects.update_or_create(
            slug="tambores_libertacao",
            defaults={
                "name": "Tambores da Libertação",
                "master": master,
                "description": "",
                "is_active": True,
            },
        )

        Ship.objects.filter(campaign=campaign, belongs_to_crew=True, is_active=True).exclude(
            name="Caravela revolucionária de apoio"
        ).update(belongs_to_crew=False)
        Ship.objects.update_or_create(
            campaign=campaign,
            name="Caravela revolucionária de apoio",
            defaults={
                "category": "small",
                "description": (
                    "Dimensões aproximadas: 6 m de largura × 15 m de comprimento × 18 m de altura\r\n"
                    "Deques: 1\r\n"
                    "Velocidade sugerida: 8 nós, aproximadamente 16 km/h\r\n"
                    "Velocidade mínima após danos severos: 4 nós, aproximadamente 8 km/h\r\n"
                    "Munição inicial: 5 bolas de chumbo"
                ),
                "max_hp": 150,
                "current_hp": 44,
                "resistance_class": 10,
                "resistance_bonus": 10,
                "speed": "8",
                "max_crew": 20,
                "current_crew": 6,
                "navigation_resources": "adequate",
                "cannons": 1,
                "facilities": (
                    "Cabine coletiva: seis redes ou beliches apertados.\r\n"
                    "Enfermaria improvisada: pequena mesa, armário e dois leitos.\r\n"
                    "Oficina e depósito: ferramentas, madeira e peças de reposição.\r\n"
                    "Cozinha e despensa: provisões e água."
                ),
                "notes": (
                    "Estado inicial: funcional, mas antiga e com manutenção atrasada.\r\n"
                    "Capacidade de provisões: 8 dias para seis pessoas."
                ),
                "is_active": True,
                "belongs_to_crew": True,
            },
        )

        self.stdout.write(self.style.SUCCESS("Campanha e navio de desenvolvimento criados/atualizados."))
