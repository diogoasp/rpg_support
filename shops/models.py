from django.core.validators import MinValueValidator
from django.db import models


class Shop(models.Model):
    campaign = models.ForeignKey("campaigns.Campaign", on_delete=models.CASCADE, related_name="shops", verbose_name="campanha")
    name = models.CharField("nome", max_length=150)
    description = models.TextField("descrição", blank=True)
    city = models.CharField("cidade", max_length=150)
    characters = models.ManyToManyField(
        "characters.Character", through="ShopAccess", related_name="accessible_shops", blank=True
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "loja"
        verbose_name_plural = "lojas"

    def __str__(self):
        return f"{self.name} — {self.city}"


class ShopItem(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="items", verbose_name="loja")
    name = models.CharField("nome", max_length=150)
    description = models.TextField("descrição", blank=True)
    price = models.PositiveBigIntegerField("valor", validators=[MinValueValidator(0)])
    quantity = models.PositiveIntegerField("quantidade", validators=[MinValueValidator(0)])

    class Meta:
        ordering = ("name",)
        verbose_name = "item da loja"
        verbose_name_plural = "itens da loja"

    def __str__(self):
        return f"{self.name} ({self.shop.name})"


class ShopAccess(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="accesses")
    character = models.ForeignKey("characters.Character", on_delete=models.CASCADE, related_name="shop_accesses")

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "character"), name="unique_shop_character_access")]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.shop_id and self.character_id and self.shop.campaign_id != self.character.campaign_id:
            raise ValidationError("A loja e o personagem devem pertencer à mesma campanha.")
