# Standard Library
import logging
from unittest.mock import patch

# Django
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone

# AA Ledger
from ledger import tasks
from ledger.app_settings import LEDGER_CACHE_KEY
from ledger.models.planetary import CharacterPlanetDetails
from ledger.tests.testdata.generate_characteraudit import (
    create_characteraudit_from_evecharacter,
    create_update_status,
)
from ledger.tests.testdata.generate_corporationaudit import (
    create_corporation_update_status,
    create_corporationaudit_from_evecharacter,
)
from ledger.tests.testdata.generate_planets import (
    _planetary_data,
    create_character_planet,
    create_character_planet_details,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse

TASK_PATH = "ledger.tasks"


@patch(TASK_PATH + ".update_character", spec=True)
class TestUpdateAllCharacters(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()

        cls.audit = create_characteraudit_from_evecharacter(1001)

    def test_should_update_all_characters(self, mock_update_character):
        # when
        tasks.update_all_characters()
        # then
        self.assertTrue(mock_update_character.apply_async.called)

    def test_should_update_subset_characters(self, mock_update_character):
        # when
        tasks.update_subset_characters()
        # then
        self.assertTrue(mock_update_character.apply_async.called)


@patch(TASK_PATH + ".chain", spec=True)
@patch(TASK_PATH + ".logger", spec=True)
class TestUpdateCharacter(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()

        cls.audit = create_characteraudit_from_evecharacter(1001)

    def test_update_character_should_no_updated(self, mock_logger, __):
        # given
        for section in self.audit.UpdateSection.get_sections():
            create_update_status(
                self.audit,
                section=section,
                is_success=True,
                error_message="",
                has_token_error=False,
                last_run_at=timezone.now(),
                last_run_finished_at=timezone.now(),
                last_update_at=timezone.now(),
                last_update_finished_at=timezone.now(),
            )

        # when
        tasks.update_character(self.audit.pk)
        # then
        mock_logger.info.assert_called_once_with(
            "No updates needed for %s",
            self.audit.eve_character.character_name,
        )

    def test_update_character_should_update(self, mock_logger, mock_chain):
        # given
        create_update_status(
            self.audit,
            section=self.audit.UpdateSection.WALLET_JOURNAL,
            is_success=True,
            error_message="",
            has_token_error=False,
            last_run_at=None,
            last_run_finished_at=None,
            last_update_at=None,
            last_update_finished_at=None,
        )

        # when
        tasks.update_character(self.audit.pk)
        # then
        mock_chain.assert_called_once()


@patch(TASK_PATH + ".update_corporation", spec=True)
class TestUpdateAllCorporations(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()

        cls.audit = create_corporationaudit_from_evecharacter(1001)

    def test_should_update_all_corporations(self, mock_update_corporation):
        # when
        tasks.update_all_corporations()
        # then
        self.assertTrue(mock_update_corporation.apply_async.called)

    def test_should_update_subset_corporation(self, mock_update_corporation):
        # when
        tasks.update_subset_corporations()
        # then
        self.assertTrue(mock_update_corporation.apply_async.called)


@patch(TASK_PATH + ".chain", spec=True)
@patch(TASK_PATH + ".logger", spec=True)
class TestUpdateCorporation(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()

        cls.audit = create_corporationaudit_from_evecharacter(1001)

    def test_update_corporation_should_no_updated(self, mock_logger, __):
        # given
        for section in self.audit.UpdateSection.get_sections():
            create_corporation_update_status(
                self.audit,
                section=section,
                is_success=True,
                error_message="",
                has_token_error=False,
                last_run_at=timezone.now(),
                last_run_finished_at=timezone.now(),
                last_update_at=timezone.now(),
                last_update_finished_at=timezone.now(),
            )
        # when
        tasks.update_corporation(self.audit.pk)
        # then
        mock_logger.info.assert_called_once_with(
            "No updates needed for %s",
            self.audit.corporation.corporation_name,
        )

    def test_update_corporation_should_update(self, mock_logger, mock_chain):
        # given
        create_corporation_update_status(
            self.audit,
            section=self.audit.UpdateSection.WALLET_JOURNAL,
            is_success=True,
            error_message="",
            has_token_error=False,
            last_run_at=None,
            last_run_finished_at=None,
            last_update_at=None,
            last_update_finished_at=None,
        )

        # when
        tasks.update_corporation(self.audit.pk)
        # then
        mock_chain.assert_called_once()


@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    APP_UTILS_OBJECT_CACHE_DISABLED=True,
)
@patch(TASK_PATH + ".logger", spec=True)
class TestClearEtag(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()

    def test_clear_all_etag_return_no_etags(self, mock_logger):
        # when
        tasks.clear_all_etags()

        # then
        mock_logger.info.assert_any_call("Deleting %s etag keys", 0)
        mock_logger.info.assert_any_call("No etag keys to delete")

    def test_clear_all_etag_return_etags(self, mock_logger):
        # given
        # pylint: disable=import-outside-toplevel
        # Third Party
        from django_redis import get_redis_connection

        _client = get_redis_connection("default")
        keys = _client.keys(f":?:{LEDGER_CACHE_KEY}-*")

        # when
        tasks.clear_all_etags()

        # then
        mock_logger.info.assert_any_call("Deleting %s etag keys", len(keys))
        mock_logger.info.assert_any_call("Deleted %s etag keys", len(keys))


@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    APP_UTILS_OBJECT_CACHE_DISABLED=True,
)
class TestCheckPlanetaryNotification(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.planet_params = {
            "upgrade_level": 5,
            "num_pins": 5,
        }

        cls.planetdetails_params = {
            "pin_id": 1,
            "pin_type": "Extractor",
            "status": "Active",
            "last_update": None,
            "last_update_finished_at": None,
        }

        cls.audit = create_characteraudit_from_evecharacter(1001)

        cls.audit2 = create_characteraudit_from_evecharacter(1002)

        cls.planet_1 = create_character_planet(
            cls.audit, planet_id=4001, **cls.planet_params
        )

        cls.planet_2 = create_character_planet(
            cls.audit2, planet_id=4001, **cls.planet_params
        )

        cls.planet_3 = create_character_planet(
            cls.audit2, planet_id=4002, **cls.planet_params
        )

        cls.planetdetails_1 = create_character_planet_details(
            cls.planet_1, notification=True, **_planetary_data
        )

        cls.planetdetails_2 = create_character_planet_details(
            cls.planet_2,
            notification=True,
        )

        cls.planetdetails_3 = create_character_planet_details(
            cls.planet_3, notification=True, **_planetary_data
        )

    def test_check_planetary_notification(self):
        # when
        tasks.check_planetary_alarms()
        # then
        self.assertEqual(
            CharacterPlanetDetails.objects.filter(
                notification_sent=True,
            ).count(),
            2,
        )
