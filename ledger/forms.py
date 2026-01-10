"""Forms for app."""

# Django
from django import forms
from django.utils.translation import gettext_lazy as _

# AA Ledger
from ledger.models.characteraudit import CharacterWalletJournalEntry
from ledger.models.corporationaudit import (
    CorporationWalletDivision,
    CorporationWalletJournalEntry,
)

from .constants import DayChoice, MonthChoice


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

    def to_python(self, value):
        # Treat "0" as the empty selection (All Divisions)
        if value in (None, "", "0"):
            return None
        return super().to_python(value)


class YearlyModelChoiceField(forms.TypedChoiceField):
    """TypeChoiceField for selecting a year built from date objects."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("coerce", int)
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj) -> str:
        return f"{obj}"


class DropdownFormBaseModel(forms.Form):
    """Base form for dropdown selectors."""

    year = YearlyModelChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(attrs={"class": "btn btn-secondary form-select me-2"}),
    )

    month = forms.TypedChoiceField(
        choices=[(None, _("All Months"))] + list(MonthChoice.choices),
        required=False,
        coerce=int,
        empty_value=None,
        widget=forms.Select(attrs={"class": "btn btn-secondary form-select me-2"}),
    )

    day = forms.TypedChoiceField(
        choices=[(None, _("All Days"))] + list(DayChoice.choices),
        required=False,
        coerce=int,
        empty_value=None,
        widget=forms.Select(attrs={"class": "btn btn-secondary form-select me-2"}),
    )


class CharacterDropdownForm(DropdownFormBaseModel):
    """Form for ledger dropdown selector."""

    def __init__(self, *args, character_id, year=None, month=None, day=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate the year field with distinct years from the journal entries
        years_qs = (
            CharacterWalletJournalEntry.objects.filter(
                character__eve_character__character_id=character_id
            )
            .exclude(date__year__isnull=True)
            .values_list("date__year", flat=True)
            .order_by("-date__year")
            .distinct()
        )

        year_choices = [(str(y), str(y)) for y in years_qs]
        self.fields["year"].choices = year_choices

        # Set initial selections if provided
        if year is not None:
            self.fields["year"].initial = str(year)
        if month is not None and "month" in self.fields:
            self.fields["month"].initial = str(month)
        if day is not None and "day" in self.fields:
            self.fields["day"].initial = str(day)


class CorporationDropdownForm(DropdownFormBaseModel):
    """Form for ledger dropdown selector."""

    def __init__(
        self,
        *args,
        corporation_id,
        division_id=None,
        year=None,
        month=None,
        day=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        # Set the division queryset based on the corporation_id
        div_qs = CorporationWalletDivision.objects.filter(
            corporation__eve_corporation__corporation_id=corporation_id
        ).order_by("division_id")
        self.fields["division"].queryset = div_qs
        # Make sure "All Divisions" uses value "0"
        div_choices = [(None, _("All Divisions"))] + [
            (str(d.pk), d.name or "") for d in div_qs
        ]
        self.fields["division"].choices = div_choices

        # Populate the year field with distinct years from the journal entries
        years_qs = (
            CorporationWalletJournalEntry.objects.filter(
                division__corporation__eve_corporation__corporation_id=corporation_id
            )
            .exclude(date__year__isnull=True)
            .values_list("date__year", flat=True)
            .order_by("-date__year")
            .distinct()
        )

        year_choices = [(str(y), str(y)) for y in years_qs]
        self.fields["year"].choices = year_choices

        # Set initial selections if provided
        if division_id is not None:
            self.fields["division"].initial = division_id
        if year is not None:
            self.fields["year"].initial = year
        if month is not None and "month" in self.fields:
            self.fields["month"].initial = month
        if day is not None and "day" in self.fields:
            self.fields["day"].initial = day

    division = DivisionModelChoiceField(
        queryset=CorporationWalletDivision.objects.none(),
        required=False,
        empty_label=None,
        widget=forms.Select(attrs={"class": "btn btn-secondary form-select me-2"}),
    )


class AllianceDropdownForm(DropdownFormBaseModel):
    """Form for ledger dropdown selector."""

    def __init__(
        self,
        *args,
        alliance_id,
        year=None,
        month=None,
        day=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        # Populate the year field with distinct years from the journal entries
        years_qs = (
            CorporationWalletJournalEntry.objects.filter(
                division__corporation__eve_corporation__alliance__alliance_id=alliance_id
            )
            .exclude(date__year__isnull=True)
            .values_list("date__year", flat=True)
            .order_by("-date__year")
            .distinct()
        )

        year_choices = [(str(y), str(y)) for y in years_qs]
        self.fields["year"].choices = year_choices

        if year is not None:
            self.fields["year"].initial = year
        if month is not None and "month" in self.fields:
            self.fields["month"].initial = month
        if day is not None and "day" in self.fields:
            self.fields["day"].initial = day
