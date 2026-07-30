from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse

from campaigns.models import Campaign
from characters.models import Character
from inventory.models import InventoryItem
from shops.models import Shop, ShopAccess, ShopItem
from shops.services import purchase


class ShopFlowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.master = User.objects.create_user(username="master", password="pw", role="master")
        self.player = User.objects.create_user(username="player", password="pw", role="player")
        self.other = User.objects.create_user(username="other", password="pw", role="player")
        self.campaign = Campaign.objects.create(name="East Blue", slug="east-blue", master=self.master)
        self.campaign.players.add(self.player)
        self.character = Character.objects.create(
            campaign=self.campaign, user=self.player, name="Nami", money=100,
            max_hp=10, current_hp=10,
        )
        self.shop = Shop.objects.create(campaign=self.campaign, name="Mercado", description="Tudo", city="Loguetown")
        self.item = ShopItem.objects.create(shop=self.shop, name="Mapa", description="Mapa marítimo", price=30, quantity=2)

    def test_purchase_is_atomic_and_adds_item_to_inventory(self):
        ShopAccess.objects.create(shop=self.shop, character=self.character)

        purchase(actor=self.player, item_id=self.item.pk)

        self.character.refresh_from_db()
        self.item.refresh_from_db()
        inventory_item = InventoryItem.objects.get(character=self.character, name="Mapa")
        self.assertEqual(self.character.money, 70)
        self.assertEqual(self.item.quantity, 1)
        self.assertEqual(inventory_item.quantity, 1)

    def test_purchase_requires_access_and_enough_money(self):
        with self.assertRaises(PermissionDenied):
            purchase(actor=self.player, item_id=self.item.pk)
        ShopAccess.objects.create(shop=self.shop, character=self.character)
        self.character.money = 10
        self.character.save(update_fields=("money",))
        with self.assertRaisesMessage(ValidationError, "Bellys insuficientes"):
            purchase(actor=self.player, item_id=self.item.pk)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 2)

    def test_master_can_toggle_access_only_in_own_campaign(self):
        self.client.force_login(self.master)
        url = reverse("shops:toggle_access", args=(self.shop.pk, self.character.pk))
        self.assertRedirects(self.client.post(url), reverse("dashboard:master"))
        self.assertTrue(ShopAccess.objects.filter(shop=self.shop, character=self.character).exists())
        self.client.post(url)
        self.assertFalse(ShopAccess.objects.filter(shop=self.shop, character=self.character).exists())

    def test_player_only_sees_released_shops(self):
        self.client.force_login(self.player)
        response = self.client.get(reverse("shops:list"))
        self.assertNotContains(response, "Loguetown")
        ShopAccess.objects.create(shop=self.shop, character=self.character)
        response = self.client.get(reverse("shops:list"))
        self.assertContains(response, "Mercado")
        self.assertContains(response, "Mapa")

    def test_removed_campaign_member_cannot_see_or_purchase_released_shop(self):
        ShopAccess.objects.create(shop=self.shop, character=self.character)
        self.campaign.players.remove(self.player)

        self.client.force_login(self.player)
        response = self.client.get(reverse("shops:list"))

        self.assertNotContains(response, "Loguetown")
        self.assertNotContains(response, "Mapa marítimo")
        with self.assertRaises(PermissionDenied):
            purchase(actor=self.player, item_id=self.item.pk)
        self.item.refresh_from_db()
        self.character.refresh_from_db()
        self.assertEqual(self.item.quantity, 2)
        self.assertEqual(self.character.money, 100)

    def test_purchase_handles_duplicate_matching_inventory_items(self):
        ShopAccess.objects.create(shop=self.shop, character=self.character)
        first = InventoryItem.objects.create(
            character=self.character,
            name=self.item.name,
            description=self.item.description,
            quantity=4,
            is_visible=True,
        )
        second = InventoryItem.objects.create(
            character=self.character,
            name=self.item.name,
            description=self.item.description,
            quantity=7,
            is_visible=True,
        )

        purchase(actor=self.player, item_id=self.item.pk)

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.quantity, 5)
        self.assertEqual(second.quantity, 7)
        self.assertEqual(
            InventoryItem.objects.filter(
                character=self.character,
                name=self.item.name,
                description=self.item.description,
                is_active=True,
            ).count(),
            2,
        )

    def test_purchase_makes_matching_hidden_inventory_item_visible(self):
        ShopAccess.objects.create(shop=self.shop, character=self.character)
        inventory_item = InventoryItem.objects.create(
            character=self.character,
            name=self.item.name,
            description=self.item.description,
            quantity=1,
            is_visible=False,
        )

        purchase(actor=self.player, item_id=self.item.pk)

        inventory_item.refresh_from_db()
        self.assertEqual(inventory_item.quantity, 2)
        self.assertTrue(inventory_item.is_visible)
