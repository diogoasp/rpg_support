from django.conf import settings
from django.db import models
from django.urls import reverse


class Campaign(models.Model):
    name = models.CharField("nome", max_length=150)
    slug = models.SlugField(unique=True)
    description = models.TextField("descrição", blank=True)
    cover_image = models.ImageField("imagem de capa", upload_to="campaigns/covers/", blank=True)
    master = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="mastered_campaigns",
        limit_choices_to={"role": "master"},
    )
    players = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="campaigns",
        limit_choices_to={"role": "player"},
    )
    is_active = models.BooleanField("ativa", default=True)
    created_at = models.DateTimeField("criada em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizada em", auto_now=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "campanha"
        verbose_name_plural = "campanhas"

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("campaigns:detail", kwargs={"slug": self.slug})

    def has_member(self, user: settings.AUTH_USER_MODEL) -> bool:
        if not user.is_authenticated:
            return False
        return self.master_id == user.pk or self.players.filter(pk=user.pk).exists()
