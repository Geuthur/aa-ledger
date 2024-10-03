from datetime import timedelta
from unittest.mock import MagicMock, call, patch

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from esi.errors import TokenExpiredError
from eveuniverse.models import EvePlanet

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter
from app_utils.testing import add_character_to_user, create_user_from_evecharacter

from ledger.models.characteraudit import CharacterAudit
from ledger.models.corporationaudit import CorporationAudit
from ledger.models.planetary import CharacterPlanet, CharacterPlanetDetails
from ledger.tasks import (
    check_planetary_alarms,
    create_member_audit,
    create_missing_character,
    update_all_characters,
    update_all_corps,
    update_char_mining_ledger,
    update_char_planets,
    update_char_planets_details,
    update_char_wallet,
    update_character,
    update_corp,
    update_corp_wallet,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all
from ledger.tests.testdata.load_planetary import load_planetary

MODULE_PATH = "ledger.tasks"


class TestTasks(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()
        load_planetary()

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
            ],
        )

        cls.user2, cls.character_ownership2 = create_user_from_evecharacter(
            1002,
            permissions=[
                "ledger.basic_access",
            ],
        )

        cls.token = cls.user.token_set.first()
        cls.corporation = cls.character_ownership.character.corporation

    @patch(MODULE_PATH + ".EveCharacter.objects.create_character")
    def test_create_character(self, _):
        # given
        chars_list = [1010, 1011]
        # when
        result = create_missing_character(chars_list=chars_list)
        # then
        self.assertTrue(result)

    @patch(MODULE_PATH + ".EveCharacter.objects.create_character")
    def test_create_character_integrity(self, mock_character):
        # given
        chars_list = [1001, 1011]
        mock_character.side_effect = [IntegrityError("duplicate key"), None]
        # when
        result = create_missing_character(chars_list=chars_list)
        # then
        self.assertTrue(result)

    @patch(MODULE_PATH + ".update_character.apply_async")
    @patch(MODULE_PATH + ".logger")
    def test_update_all_characters(self, mock_logger, mock_update_character):
        # given
        characters_count = CharacterAudit.objects.count()
        # when
        update_all_characters()
        # then
        self.assertEqual(mock_update_character.call_count, characters_count)
        mock_logger.info.assert_called_once_with(
            "Queued %s Char Audit Updates", characters_count
        )

    @patch(MODULE_PATH + ".CharacterAudit.objects.select_related")
    def test_update_character(self, mock_select_related):
        # given
        mock_character = MagicMock()
        mock_character.last_update_mining = timezone.now()
        mock_character.last_update_wallet = timezone.now()
        mock_character.last_update_planetary = timezone.now()
        mock_character.character = MagicMock()
        mock_character.character.character_id = self.token.character_id
        mock_character.character.character_name = self.token.character_name

        mock_filter = MagicMock()
        mock_filter.first.return_value = mock_character
        mock_select_related.return_value.filter.return_value = mock_filter
        # when
        result = update_character(self.token.character_id)
        # then
        self.assertTrue(result)

    @patch(MODULE_PATH + ".update_character_mining")
    def test_update_character_mining(self, mock_char_mining):
        # given
        expected_return_value = f"Finished Mining for: {self.token.character_name}"
        mock_char_mining.return_value = expected_return_value
        # when
        result = update_char_mining_ledger(self.token.character_id)
        # then
        self.assertTrue(mock_char_mining.called)
        self.assertEqual(expected_return_value, result)

    @patch(MODULE_PATH + ".update_character_wallet")
    def test_update_character_wallet(self, mock_char_wallet):
        # given
        expected_return_value = (
            f"Finished wallet transactions for: {self.token.character_name}"
        )
        mock_char_wallet.return_value = expected_return_value
        # when
        result = update_char_wallet(self.token.character_id)
        # then
        self.assertTrue(mock_char_wallet.called)
        self.assertEqual(expected_return_value, result)

    @patch(MODULE_PATH + ".update_char_mining_ledger.si")
    @patch(MODULE_PATH + ".update_char_wallet.si")
    @patch(MODULE_PATH + ".Token.get_token")
    @patch(MODULE_PATH + ".EveCharacter.objects.get_character_by_id")
    @patch(MODULE_PATH + ".CharacterAudit.objects.update_or_create")
    @patch(MODULE_PATH + ".CharacterAudit.objects.select_related")
    def test_update_character_from_token(
        self,
        mock_check_char,
        mock_update_or_create,
        mock_get_character_by_id,
        mock_get_token,
        mock_char_wallet,
        mock_char_mining,
    ):
        # given
        mock_check_char.return_value.filter.return_value.first.return_value = None
        mock_token = MagicMock()
        mock_token.valid_access_token.return_value = True
        mock_get_token.return_value = mock_token
        mock_character = MagicMock()
        mock_character.last_update_mining = timezone.now() - timedelta(days=1)
        mock_character.last_update_wallet = timezone.now() - timedelta(days=1)
        mock_character.last_update_planetary = timezone.now() - timedelta(days=1)
        mock_update_or_create.return_value = (mock_character, True)
        # when
        update_character(self.token.character_id)
        # then
        mock_get_token.assert_called_once_with(
            self.token.character_id, CharacterAudit.get_esi_scopes()
        )
        mock_token.valid_access_token.assert_called_once()
        mock_get_character_by_id.assert_called_once_with(mock_token.character_id)
        mock_update_or_create.assert_called_once()
        self.assertTrue(mock_char_wallet.called)
        self.assertTrue(mock_char_mining.called)

    @patch(MODULE_PATH + ".Token.get_token")
    @patch(MODULE_PATH + ".CharacterAudit.objects.update_or_create")
    @patch(MODULE_PATH + ".CharacterAudit.objects.select_related")
    def test_update_character_token_expired_token(
        self, mock_check_char, mock_update_or_create, mock_get_token
    ):
        # given
        mock_check_char.return_value.filter.return_value.first.return_value = None
        mock_token = MagicMock()
        mock_token.valid_access_token.side_effect = TokenExpiredError
        mock_get_token.return_value = mock_token
        mock_character = MagicMock()
        mock_update_or_create.return_value = (mock_character, True)
        # when
        result = update_character(self.token.character_id)
        # then
        self.assertFalse(result)
        mock_get_token.assert_called_once_with(
            self.token.character_id, CharacterAudit.get_esi_scopes()
        )
        mock_token.valid_access_token.assert_called_once()

    @patch(MODULE_PATH + ".Token.get_token")
    @patch(MODULE_PATH + ".CharacterAudit.objects.select_related")
    def test_update_character_token_no_access_token(
        self, mock_check_char, mock_get_token
    ):
        # given
        mock_check_char.return_value.filter.return_value.first.return_value = None
        mock_token = MagicMock()
        mock_token.valid_access_token.return_value = False
        mock_get_token.return_value = mock_token
        # when
        result = update_character(self.token.character_id)
        # then
        mock_token.valid_access_token.assert_called_once()
        self.assertFalse(result)

    @patch(MODULE_PATH + ".Token.get_token")
    @patch(MODULE_PATH + ".CharacterAudit.objects.select_related")
    @patch(MODULE_PATH + ".logger")
    def test_update_character_token_no_token(
        self, mock_logger, mock_check_char, mock_get_token
    ):
        # given
        mock_check_char.return_value.filter.return_value.first.return_value = None
        mock_get_token.return_value = False
        # when
        result = update_character(self.token.character_id)
        # then
        self.assertFalse(result)
        mock_logger.info.assert_called_once_with("No Tokens for %s", 1001)

    @patch(MODULE_PATH + ".update_corp.apply_async")
    @patch(MODULE_PATH + ".logger")
    def test_update_all_cors(self, mock_logger, mock_update_character):
        # given
        corporation_count = CorporationAudit.objects.count()
        # when
        update_all_corps()
        # then
        self.assertEqual(mock_update_character.call_count, corporation_count)
        mock_logger.info.assert_called_once_with(
            "Queued %s Corp Audit Updates", corporation_count
        )

    @patch(MODULE_PATH + ".update_corp_wallet.si")
    def test_update_corp(self, mock_corp_wallet):
        # when
        update_corp(self.corporation.corporation_id)
        # then
        self.assertTrue(mock_corp_wallet.called)

    @patch(MODULE_PATH + ".update_corp_wallet_division")
    def test_update_corp_wallet(self, mock_corp_wallet_division):
        # given
        expected_return_value = (
            f"Finished wallet divs for: {self.corporation.corporation_name}"
        )
        mock_corp_wallet_division.return_value = expected_return_value
        # when
        result = update_corp_wallet(self.corporation.corporation_id)
        # then
        self.assertTrue(mock_corp_wallet_division.called)
        self.assertEqual(expected_return_value, result)

    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects.all")
    @patch(MODULE_PATH + ".CharacterOwnership.objects.get")
    @patch(MODULE_PATH + ".notify")
    def test_no_expired_alarms(self, mock_notify, mock_get_ownership, mock_all_planets):
        # Setup mock return values
        mock_all_planets.return_value = []

        # Call the function
        check_planetary_alarms()

        # Check that notify was not called
        mock_notify.assert_not_called()

    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects.all")
    @patch(MODULE_PATH + ".CharacterOwnership.objects.get")
    @patch(MODULE_PATH + ".notify")
    def test_expired_alarms_notification_sent(
        self, mock_notify, mock_get_ownership, mock_all_planets
    ):
        # Setup mock return values
        planet = MagicMock()
        planet.is_expired.return_value = True
        planet.notification_sent = False
        planet.notification = True
        planet.planet.character.character.character_id = 1999
        planet.planet.character.character.character_name = "Test Character"
        planet.planet.planet.name = "Test Planet"
        mock_all_planets.return_value = [planet]

        owner = MagicMock()
        owner.user.profile.main_character.character_id = 1999
        owner.user.profile.main_character.character_ownership.user.character_ownerships.all.return_value.values_list.return_value = [
            1999
        ]
        mock_get_ownership.return_value = owner

        # Call the function
        check_planetary_alarms()

        # Check that notify was called
        mock_notify.assert_called_once()
        planet.save.assert_called_once()

    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects.all")
    @patch(MODULE_PATH + ".CharacterOwnership.objects.get")
    @patch(MODULE_PATH + ".notify")
    def test_expired_alarms_notification_already_sent(
        self, mock_notify, mock_get_ownership, mock_all_planets
    ):
        # Setup mock return values
        planet = MagicMock()
        planet.is_expired.return_value = True
        planet.notification_sent = True
        planet.notification = True
        mock_all_planets.return_value = [planet]

        # Call the function
        check_planetary_alarms()

        # Check that notify was not called
        mock_notify.assert_not_called()
        planet.save.assert_not_called()

    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects.all")
    @patch(MODULE_PATH + ".CharacterOwnership.objects.get")
    @patch(MODULE_PATH + ".notify")
    def test_notification_message_format(
        self, mock_notify, mock_get_ownership, mock_all_planets
    ):
        # Setup mock return values
        planet = MagicMock()
        planet.is_expired.return_value = True
        planet.notification_sent = False
        planet.notification = True
        planet.planet.character.character.character_id = 1999
        planet.planet.character.character.character_name = "Test Character"
        planet.planet.planet.name = "Test Planet"
        mock_all_planets.return_value = [planet]

        owner = MagicMock()
        owner.user.profile.main_character.character_id = 1999
        owner.user.profile.main_character.character_ownership.user.character_ownerships.all.return_value.values_list.return_value = [
            1999
        ]
        mock_get_ownership.return_value = owner

        # Call the function
        check_planetary_alarms()

        # Check that notify was called with correct message
        expected_message = format_html(
            "Following Planet Extractor Heads have expired: \n{}",
            "Test Character on Test Planet",
        )
        mock_notify.assert_called_once_with(
            title=_("Planetary Extractor Heads Expired"),
            message=expected_message,
            user=owner.user,
            level="warning",
        )
        planet.save.assert_called_once()

    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects.all")
    @patch(MODULE_PATH + ".CharacterOwnership.objects.get")
    @patch(MODULE_PATH + ".notify")
    def test_main_id_set(self, mock_notify, mock_get_ownership, mock_all_planets):
        # Setup mock return values
        planet = MagicMock()
        planet.is_expired.return_value = True
        planet.notification_sent = False
        planet.notification = True
        planet.planet.character.character.character_id = 1999
        planet.planet.character.character.character_name = "Test Character"
        planet.planet.planet.name = "Test Planet"
        mock_all_planets.return_value = [planet]

        owner = MagicMock()
        owner.user.profile.main_character.character_id = 1999
        owner.user.profile.main_character.character_ownership.user.character_ownerships.all.return_value.values_list.return_value = [
            1999
        ]
        mock_get_ownership.return_value = owner

        # Call the function
        check_planetary_alarms()

        # Check that notify was called with correct message
        expected_message = format_html(
            "Following Planet Extractor Heads have expired: \n{}",
            "Test Character on Test Planet",
        )
        mock_notify.assert_called_once_with(
            title=_("Planetary Extractor Heads Expired"),
            message=expected_message,
            user=owner.user,
            level="warning",
        )
        planet.save.assert_called_once()

        # Verify that main_id was set correctly
        self.assertEqual(owner.user.profile.main_character.character_id, 1999)

    @patch(MODULE_PATH + ".update_character_planetary")
    def test_update_char_planets(self, mock_char_planet):
        # given
        expected_return_value = ("Finished planets update for: %s", "Gneuten")
        mock_char_planet.return_value = expected_return_value
        # when
        result = update_char_planets(self.token.character_id)
        # then
        self.assertTrue(mock_char_planet.called)
        self.assertEqual(expected_return_value, result)

    @patch(MODULE_PATH + ".update_character_planetary_details")
    def test_update_char_planets_details(self, mock_char_planetdetails):
        # given
        expected_return_value = ("Finished planets data update for: %s", "Gneuten")
        mock_char_planetdetails.return_value = expected_return_value
        # when
        result = update_char_planets_details(1001, 4001)
        # then
        self.assertTrue(mock_char_planetdetails.called)
        self.assertEqual(expected_return_value, result)

    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects.all")
    @patch(MODULE_PATH + ".CharacterOwnership.objects.get")
    @patch(MODULE_PATH + ".notify")
    def test_check_planetary_alarms_many(
        self, mock_notify, mock_get_ownership, mock_all_planets
    ):
        # Setup mock return values
        planet = MagicMock()
        planet.is_expired.return_value = True
        planet.notification_sent = False
        planet.notification = True
        planet.planet.character.character.character_id = 1001
        planet.planet.character.character.character_name = "Gneuten"
        planet.planet.planet.name = "Test Planet I"

        planet2 = MagicMock()
        planet2.is_expired.return_value = True
        planet2.notification_sent = False
        planet2.notification = True
        planet2.planet.character.character.character_id = 1001
        planet2.planet.character.character.character_name = "Gneuten"
        planet2.planet.planet.name = "Test Planet II"

        mock_all_planets.return_value = [planet, planet2]

        mock_get_ownership.return_value = self.character_ownership

        # Call the function
        check_planetary_alarms()

        # Check that notify was called with correct message
        expected_message = format_html(
            "Following Planet Extractor Heads have expired: \n{}\n{}",
            "Gneuten on Test Planet I",
            "Gneuten on Test Planet II",
        )
        mock_notify.assert_called_once_with(
            title=_("Planetary Extractor Heads Expired"),
            message=expected_message,
            user=self.user,
            level="warning",
        )
        planet.save.assert_called_once()

    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects.all")
    @patch(MODULE_PATH + ".CharacterOwnership.objects.get")
    @patch(MODULE_PATH + ".notify")
    def test_character_ownership_does_not_exist(
        self, mock_notify, mock_get_ownership, mock_all_planets
    ):
        # Setup mock return values
        planet = MagicMock()
        planet.is_expired.return_value = True
        planet.notification_sent = False
        planet.notification = True
        planet.planet.character.character.character_id = 1999
        mock_all_planets.return_value = [planet]

        mock_get_ownership.side_effect = CharacterOwnership.DoesNotExist

        # Call the function
        check_planetary_alarms()

        # Check that notify was not called
        mock_notify.assert_not_called()
        planet.save.assert_not_called()

    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects.all")
    @patch(MODULE_PATH + ".CharacterOwnership.objects.get")
    @patch(MODULE_PATH + ".notify")
    def test_attribute_error(self, mock_notify, mock_get_ownership, mock_all_planets):
        # Setup mock return values
        planet = MagicMock()
        planet.is_expired.return_value = True
        planet.notification_sent = False
        planet.notification = True
        planet.planet.character.character.character_id = 1999
        mock_all_planets.return_value = [planet]

        mock_get_ownership.side_effect = AttributeError

        # Call the function
        check_planetary_alarms()

        # Check that notify was not called
        mock_notify.assert_not_called()
        planet.save.assert_not_called()

    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects.all")
    @patch(MODULE_PATH + ".CharacterOwnership.objects.get")
    @patch(MODULE_PATH + ".notify")
    def test_character_id_not_in_alts(
        self, mock_notify, mock_get_ownership, mock_all_planets
    ):
        # Setup mock return values
        planet = MagicMock()
        planet.is_expired.return_value = True
        planet.notification_sent = False
        planet.notification = True
        planet.planet.character.character.character_id = 1004
        planet.planet.character.character.character_name = "Test Character"
        planet.planet.planet.name = "Test Planet I"
        mock_all_planets.return_value = [planet]

        # Setup mock return values
        planet2 = MagicMock()
        planet2.is_expired.return_value = True
        planet2.notification_sent = False
        planet2.notification = True
        planet2.planet.character.character.character_id = 1001
        planet2.planet.character.character.character_name = "Gneuten"
        planet2.planet.planet.name = "Test Planet II"

        # Setup mock return values
        planet3 = MagicMock()
        planet3.is_expired.return_value = True
        planet3.notification_sent = False
        planet3.notification = True
        planet3.planet.character.character.character_id = 1005
        planet3.planet.character.character.character_name = "Gorthd"
        planet3.planet.planet.name = "Test Planet III"

        mock_all_planets.return_value = [planet, planet2, planet3]

        owner = MagicMock()
        owner.user.profile.main_character.character_id = 1001
        owner.user.profile.main_character.character_ownership.user.character_ownerships.all.return_value.values_list.return_value = [
            1001,
            1003,
        ]
        mock_get_ownership.return_value = owner

        # Call the function
        check_planetary_alarms()

        planet.save.assert_called_once()

        # Verify that main_id was set correctly
        self.assertEqual(owner.user.profile.main_character.character_id, 1001)

    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects.all")
    @patch(MODULE_PATH + ".CharacterOwnership.objects.get")
    @patch(MODULE_PATH + ".notify")
    def test_character_id_in_alts(
        self, mock_notify, mock_get_ownership, mock_all_planets
    ):
        add_character_to_user(self.user, EveCharacter.objects.get(character_id=1002))
        # Setup mock return values
        planet = MagicMock()
        planet.is_expired.return_value = True
        planet.notification_sent = False
        planet.notification = True
        planet.planet.character.character.character_id = 1002
        planet.planet.character.character.character_name = "Gneuten"
        planet.planet.planet.name = "Test Planet I"
        mock_all_planets.return_value = [planet]

        owner = MagicMock()
        owner.user.profile.main_character.character_id = 1001
        owner.user.profile.main_character.character_ownership.user.character_ownerships.all.return_value.values_list.return_value = [
            1001,
            1002,
        ]
        mock_get_ownership.return_value = owner

        # Call the function
        check_planetary_alarms()

        # Check that notify was called with correct message
        expected_message = format_html(
            "Following Planet Extractor Heads have expired: \n{}",
            "Gneuten on Test Planet I",
        )
        mock_notify.assert_called_once_with(
            title=_("Planetary Extractor Heads Expired"),
            message=expected_message,
            user=owner.user,
            level="warning",
        )
        planet.save.assert_called_once()

        # Verify that main_id was set correctly
        self.assertEqual(owner.user.profile.main_character.character_id, 1001)
