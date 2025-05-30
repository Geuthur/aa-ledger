# Generated by Django 4.2.11 on 2024-09-11 10:28

# Django
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "ledger",
            "0004_characteraudit_last_update_planetary_characterplanet_and_more",
        ),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="corporationaudit",
            options={
                "default_permissions": (),
                "permissions": (
                    ("corp_audit_admin_manager", "Has access to all Corporations"),
                ),
            },
        ),
        migrations.AlterModelOptions(
            name="general",
            options={
                "default_permissions": (),
                "managed": False,
                "permissions": (
                    ("basic_access", "Can access this app, Ledger."),
                    ("advanced_access", "Can access Corporation and Alliance Ledger."),
                    ("admin_access", "Has access to all Administration tools"),
                ),
            },
        ),
    ]
