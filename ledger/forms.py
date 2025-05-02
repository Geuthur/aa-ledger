"""Forms for app."""

# Django
from django import forms


class ConfirmForm(forms.Form):
    """Form Confirms."""

    character_id = forms.CharField(
        widget=forms.HiddenInput(),
    )

    planet_id = forms.CharField(
        widget=forms.HiddenInput(),
    )
