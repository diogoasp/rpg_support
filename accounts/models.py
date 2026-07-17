from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        MASTER = "master", "Mestre"
        PLAYER = "player", "Jogador"

    role = models.CharField(max_length=20, choices=Role.choices)

    @property
    def is_master(self) -> bool:
        return self.role == self.Role.MASTER

    @property
    def is_player(self) -> bool:
        return self.role == self.Role.PLAYER
