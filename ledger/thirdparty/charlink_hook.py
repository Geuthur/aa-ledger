# Third Party
from charlink.app_imports.utils import AppImport, LoginImport

# Django
from django.contrib.auth.models import Permission, User
from django.db.models import Exists, OuterRef
from django.utils.translation import gettext_lazy as trans

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

# Alliance Auth (External Libs)
from app_utils.allianceauth import users_with_permission

# AA Ledger
from ledger.app_settings import LEDGER_APP_NAME
from ledger.models.characteraudit import CharacterAudit
from ledger.models.corporationaudit import CorporationAudit
from ledger.tasks import update_character, update_corporation

_corp_perms = [
    "ledger.manage_access",
]


# pylint: disable=unused-argument, duplicate-code
def _add_character_charaudit(request, token):
    character = CharacterAudit.objects.update_or_create(
        eve_character=EveCharacter.objects.get_character_by_id(token.character_id),
        defaults={
            "character_name": token.character_name,
        },
    )[0]
    update_character.apply_async(
        args=[character.pk], kwargs={"force_refresh": True}, priority=6
    )


# pylint: disable=unused-argument, duplicate-code
def _add_character_corp(request, token):
    char = EveCharacter.objects.get_character_by_id(token.character_id)
    eve_corp, _ = EveCorporationInfo.objects.get_or_create(
        corporation_id=char.corporation_id,
        defaults={
            "member_count": 0,
            "corporation_ticker": char.corporation_ticker,
            "corporation_name": char.corporation_name,
        },
    )
    corp = CorporationAudit.objects.update_or_create(
        corporation=eve_corp,
        defaults={
            "corporation_name": eve_corp.corporation_name,
        },
    )[0]
    update_corporation.apply_async(
        args=[corp.pk], kwargs={"force_refresh": True}, priority=6
    )


def _check_perms_corp(user: User):
    return any(user.has_perm(perm) for perm in _corp_perms)


def _is_character_added_charaudit(character: EveCharacter):
    return CharacterAudit.objects.filter(character=character).exists()


def _is_character_added_corp(character: EveCharacter):
    return CorporationAudit.objects.filter(
        corporation__corporation_id=character.corporation_id
    ).exists()


def _users_with_perms_charaudit():
    return users_with_permission(
        Permission.objects.get(
            content_type__app_label="ledger", codename="basic_access"
        )
    )


def _users_with_perms_corp():
    users = users_with_permission(
        Permission.objects.get(
            content_type__app_label=_corp_perms[0].split(".", maxsplit=1)[0],
            codename=_corp_perms[0].split(".", maxsplit=1)[1],
        )
    )
    for perm_str in _corp_perms[1:]:
        users |= users_with_permission(
            Permission.objects.get(
                content_type__app_label=perm_str.split(".", maxsplit=1)[0],
                codename=perm_str.split(".", maxsplit=1)[1],
            )
        )

    return users


app_import = AppImport(
    "ledger",
    [
        LoginImport(
            app_label="ledger",
            unique_id="default",
            field_label=LEDGER_APP_NAME + " - " + trans("Character") + " Login",
            add_character=_add_character_charaudit,
            scopes=CharacterAudit.get_esi_scopes(),
            check_permissions=lambda user: user.has_perm("ledger.basic_access"),
            is_character_added=_is_character_added_charaudit,
            is_character_added_annotation=Exists(
                CharacterAudit.objects.filter(eve_character_id=OuterRef("pk"))
            ),
            get_users_with_perms=_users_with_perms_charaudit,
        ),
        LoginImport(
            app_label="ledger",
            unique_id="corpaudit",
            field_label=LEDGER_APP_NAME + " - " + trans("Corporation") + " Login",
            add_character=_add_character_corp,
            scopes=CorporationAudit.get_esi_scopes(),
            check_permissions=_check_perms_corp,
            is_character_added=_is_character_added_corp,
            is_character_added_annotation=Exists(
                CorporationAudit.objects.filter(
                    corporation__corporation_id=OuterRef("corporation_id")
                )
            ),
            get_users_with_perms=_users_with_perms_corp,
        ),
    ],
)
