from django.core.management import call_command
from django.test import TestCase

from campaigns.models import Campaign
from ships.models import Ship


class SeedRpgTests(TestCase):
    def test_seed_rpg_creates_current_campaign_and_ship_idempotently(self):
        call_command("seed_rpg", verbosity=0)
        call_command("seed_rpg", verbosity=0)

        campaign = Campaign.objects.get(slug="tambores_libertacao")
        self.assertEqual(campaign.name, "Tambores da Libertação")
        self.assertTrue(campaign.is_active)

        ships = Ship.objects.filter(campaign=campaign, name="Caravela revolucionária de apoio")
        self.assertEqual(ships.count(), 1)

        ship = ships.get()
        self.assertEqual(ship.category, "small")
        self.assertEqual(ship.max_hp, 150)
        self.assertEqual(ship.current_hp, 44)
        self.assertEqual(ship.resistance_class, 10)
        self.assertEqual(ship.resistance_bonus, 10)
        self.assertEqual(ship.max_crew, 20)
        self.assertEqual(ship.current_crew, 6)
        self.assertEqual(ship.navigation_resources, "adequate")
        self.assertEqual(ship.cannons, 1)
        self.assertTrue(ship.is_active)
        self.assertTrue(ship.belongs_to_crew)
