from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):
    initial = True
    dependencies = [("campaigns", "0001_initial"), ("characters", "0011_character_money")]
    operations = [
        migrations.CreateModel(name="Shop", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("name", models.CharField(max_length=150, verbose_name="nome")), ("description", models.TextField(blank=True, verbose_name="descrição")), ("city", models.CharField(max_length=150, verbose_name="cidade")), ("campaign", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="shops", to="campaigns.campaign", verbose_name="campanha"))], options={"verbose_name": "loja", "verbose_name_plural": "lojas", "ordering": ("name",)}),
        migrations.CreateModel(name="ShopItem", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("name", models.CharField(max_length=150, verbose_name="nome")), ("description", models.TextField(blank=True, verbose_name="descrição")), ("price", models.PositiveBigIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name="valor")), ("quantity", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name="quantidade")), ("shop", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="shops.shop", verbose_name="loja"))], options={"verbose_name": "item da loja", "verbose_name_plural": "itens da loja", "ordering": ("name",)}),
        migrations.CreateModel(name="ShopAccess", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("character", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="shop_accesses", to="characters.character")), ("shop", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="accesses", to="shops.shop"))]),
        migrations.AddField(model_name="shop", name="characters", field=models.ManyToManyField(blank=True, related_name="accessible_shops", through="shops.ShopAccess", to="characters.character")),
        migrations.AddConstraint(model_name="shopaccess", constraint=models.UniqueConstraint(fields=("shop", "character"), name="unique_shop_character_access")),
    ]
