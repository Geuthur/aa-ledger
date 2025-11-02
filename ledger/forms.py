"""Forms for app."""

# Django
from django import forms
from django.utils.translation import gettext_lazy as _

# AA Ledger
from ledger.models.corporationaudit import (
    CorporationWalletDivision,
    CorporationWalletJournalEntry,
)


class ConfirmForm(forms.Form):
    """Form Confirms."""

    character_id = forms.CharField(
        widget=forms.HiddenInput(),
    )

    planet_id = forms.CharField(
        widget=forms.HiddenInput(),
    )


class DivisionModelChoiceField(forms.ModelChoiceField):
    """ModelChoiceField that displays "division_id - name" as the option label."""

    def label_from_instance(self, obj: CorporationWalletDivision) -> str:
        name = obj.name or ""
        return f"{name}"


class YearlyModelChoiceField(forms.TypedChoiceField):
    """TypeChoiceField for selecting a year built from date objects."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("coerce", int)
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj) -> str:
        return f"{obj}"


class GenerateDataExportForm(forms.Form):
    """Form to generate data export."""

    def __init__(self, *args, corporation_id, **kwargs):
        super().__init__(*args, **kwargs)

        # Set the division queryset based on the corporation_id
        self.fields["division"].queryset = CorporationWalletDivision.objects.filter(
            corporation__corporation__corporation_id=corporation_id
        ).order_by("division_id")

        # Populate the year field with distinct years from the journal entries
        years_qs = (
            CorporationWalletJournalEntry.objects.filter(
                division__corporation__corporation__corporation_id=corporation_id
            )
            .exclude(date__year__isnull=True)
            .values_list("date__year", flat=True)
            .order_by("-date__year")
            .distinct()
        )

        year_choices = [("", "---------")] + [(str(y), str(y)) for y in years_qs]
        self.fields["year"].choices = year_choices

    year = YearlyModelChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    MONTH_CHOICES = [
        ("", _("All months")),
        ("1", _("January")),
        ("2", _("February")),
        ("3", _("March")),
        ("4", _("April")),
        ("5", _("May")),
        ("6", _("June")),
        ("7", _("July")),
        ("8", _("August")),
        ("9", _("September")),
        ("10", _("October")),
        ("11", _("November")),
        ("12", _("December")),
    ]

    month = forms.TypedChoiceField(
        choices=MONTH_CHOICES,
        required=False,
        coerce=lambda val: (
            int(val) if val not in ("", None) else None
        ),  # Coerce to int or None
        empty_value=None,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    division = DivisionModelChoiceField(
        queryset=CorporationWalletDivision.objects.none(),
        required=False,
        empty_label=_("All Divisions"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
