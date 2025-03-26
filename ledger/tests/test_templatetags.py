from django.template import Context, Template
from django.test import TestCase, override_settings

from ledger import __version__
from ledger.view_helpers.static_files import calculate_integrity_hash


class TestVersionedStatic(TestCase):
    @override_settings(DEBUG=False)
    def test_versioned_static(self):
        context = Context(dict_={"version": __version__})
        template_to_render = Template(
            template_string=(
                "{% load ledger %}"
                "{% ledger_static 'css/ledger.css' %}"
                "{% ledger_static 'js/ledger.js' %}"
            )
        )

        rendered_template = template_to_render.render(context=context)

        expected_static_css_src = (
            f'/static/ledger/css/ledger.css?v={context["version"]}'
        )
        expected_static_css_src_integrity = calculate_integrity_hash("css/ledger.css")
        expected_static_js_src = f'/static/ledger/js/ledger.js?v={context["version"]}'
        expected_static_js_src_integrity = calculate_integrity_hash("js/ledger.js")

        self.assertIn(member=expected_static_css_src, container=rendered_template)
        self.assertIn(
            member=expected_static_css_src_integrity, container=rendered_template
        )
        self.assertIn(member=expected_static_js_src, container=rendered_template)
        self.assertIn(
            member=expected_static_js_src_integrity, container=rendered_template
        )

    @override_settings(DEBUG=True)
    def test_versioned_static_with_debug_enabled(self) -> None:
        context = Context({"version": __version__})
        template_to_render = Template(
            template_string=("{% load ledger %}" "{% ledger_static 'css/ledger.css' %}")
        )

        rendered_template = template_to_render.render(context=context)

        expected_static_css_src = (
            f'/static/ledger/css/ledger.css?v={context["version"]}'
        )

        self.assertIn(member=expected_static_css_src, container=rendered_template)
        self.assertNotIn(member="integrity=", container=rendered_template)

    @override_settings(DEBUG=False)
    def test_invalid_file_type(self) -> None:
        context = Context({"version": __version__})
        template_to_render = Template(
            template_string=(
                "{% load ledger %}" "{% ledger_static 'invalid/invalid.txt' %}"
            )
        )

        with self.assertRaises(ValueError):
            template_to_render.render(context=context)
