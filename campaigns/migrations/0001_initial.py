from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Campaign",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150, verbose_name="nome")),
                ("slug", models.SlugField(unique=True)),
                ("description", models.TextField(blank=True, verbose_name="descrição")),
                ("cover_image", models.ImageField(blank=True, upload_to="campaigns/covers/", verbose_name="imagem de capa")),
                ("is_active", models.BooleanField(default=True, verbose_name="ativa")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criada em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizada em")),
                ("master", models.ForeignKey(limit_choices_to={"role": "master"}, on_delete=django.db.models.deletion.PROTECT, related_name="mastered_campaigns", to=settings.AUTH_USER_MODEL)),
                ("players", models.ManyToManyField(blank=True, limit_choices_to={"role": "player"}, related_name="campaigns", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "campanha", "verbose_name_plural": "campanhas", "ordering": ("name",)},
        )
    ]
