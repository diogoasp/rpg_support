from django.db import migrations, models


def require_player_password_change(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(role="player", is_active=True).update(password_change_required=True)


def clear_player_password_change(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(role="player").update(password_change_required=False)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_alter_user_groups"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="password_change_required",
            field=models.BooleanField(default=False, verbose_name="troca de senha obrigatória"),
        ),
        migrations.RunPython(require_player_password_change, clear_player_password_change),
    ]
