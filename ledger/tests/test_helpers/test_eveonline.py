# Django
from django.test import TestCase
from django.utils.html import format_html

# Alliance Auth
from allianceauth.eveonline.evelinks import eveimageserver

# AA Ledger
from ledger.helpers import eveonline


class TestEveOnlineHelpers(TestCase):
    def test_urls_without_html(self):
        self.assertEqual(
            eveonline.get_character_portrait_url(1001, 64),
            eveimageserver.character_portrait_url(1001, 64),
        )
        self.assertEqual(
            eveonline.get_corporation_logo_url(2001, 64),
            eveimageserver.corporation_logo_url(2001, 64),
        )
        self.assertEqual(
            eveonline.get_alliance_logo_url(3001, 64),
            eveimageserver.alliance_logo_url(3001, 64),
        )
        self.assertEqual(
            eveonline.get_type_render_url(4001, 64),
            eveimageserver.type_render_url(4001, 64),
        )
        self.assertEqual(
            eveonline.get_icon_render_url(4001, 64),
            eveimageserver.type_icon_url(4001, 64),
        )

    def test_html_without_display_name(self):
        url = eveimageserver.character_portrait_url(1001, 32)
        self.assertEqual(
            eveonline.get_character_portrait_url(
                1001, character_name="Bob", as_html=True
            ),
            format_html(
                '<img class="character-portrait rounded-circle" src="{}" alt="{}">',
                url,
                "Bob",
            ),
        )

    def test_html_with_display_name(self):
        cases = [
            (
                eveonline.get_character_portrait_url,
                {"character_id": 1001, "character_name": "Name"},
                "character-portrait",
            ),
            (
                eveonline.get_corporation_logo_url,
                {"corporation_id": 2001, "corporation_name": "Name"},
                "corporation-logo",
            ),
            (
                eveonline.get_alliance_logo_url,
                {"alliance_id": 3001, "alliance_name": "Name"},
                "alliance-logo",
            ),
            (
                eveonline.get_type_render_url,
                {"type_id": 4001, "type_name": "Name"},
                "type-render",
            ),
            (
                eveonline.get_icon_render_url,
                {"type_id": 4001, "type_name": "Name"},
                "type-render",
            ),
        ]
        for func, kwargs, css_class in cases:
            with self.subTest(func=func.__name__):
                html = func(as_html=True, display_name=True, **kwargs)
                self.assertIn('<div class="d-flex align-items-center">', html)
                self.assertIn(f'class="{css_class} rounded-circle me-2"', html)
                self.assertIn("<span>Name</span>", html)

    def test_display_name_escapes_name(self):
        html = eveonline.get_corporation_logo_url(
            2001, corporation_name="<b>x</b>", as_html=True, display_name=True
        )
        self.assertNotIn("<b>", html)
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", html)

    def test_display_name_ignored_without_html(self):
        self.assertEqual(
            eveonline.get_alliance_logo_url(3001, display_name=True),
            eveimageserver.alliance_logo_url(3001, 32),
        )

    def test_invalid_character_id_returns_empty(self):
        self.assertEqual(eveonline.get_character_portrait_url(0, 33), "")
