# Generated by Django 4.2.11 on 2024-12-06 08:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ledger", "0005_alter_corporationaudit_options_alter_general_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="characteraudit",
            name="character_name",
            field=models.CharField(default=None, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="characterplanet",
            name="planet_name",
            field=models.CharField(default=None, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="corporationaudit",
            name="corporation_name",
            field=models.CharField(default=None, max_length=100, null=True),
        ),
    ]