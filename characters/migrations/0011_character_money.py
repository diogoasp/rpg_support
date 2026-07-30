from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("characters", "0010_character_favorite_weapon_character_hit_die_type_and_more")]
    operations = [
        migrations.AddField(
            model_name="character",
            name="money",
            field=models.PositiveBigIntegerField(default=0, verbose_name="Bellys na bolsa"),
        ),
    ]
