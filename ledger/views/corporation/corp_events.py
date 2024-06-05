"""
Corporation Events
"""

# Django
from django import forms
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.html import escape

from ledger.hooks import get_extension_logger

# Voices of War
from ledger.models.events import Events

logger = get_extension_logger(__name__)


class EventForm(forms.ModelForm):
    class Meta:
        model = Events
        fields = [
            "title",
            "date_start",
            "date_end",
            "location",
            "description",
            "char_ledger",
        ]
        widgets = {
            "date_start": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "date_end": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 6}),
            "char_ledger": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["title"].required = True
        self.fields["date_start"].required = True
        self.fields["date_end"].required = True


@login_required
@permission_required("ledger.basic_access")
def events_index(request):
    current_datetime = timezone.now()
    expired_events = Events.objects.filter(date_end__lt=current_datetime)
    future_events = Events.objects.filter(date_end__gte=current_datetime)

    return render(
        request,
        "ledger/events/index.html",
        {"expired_events": expired_events, "future_events": future_events},
    )


@login_required
@permission_required("ledger.event_admin_access")
def events_admin(request):
    events = Events.objects.all()
    return render(request, "ledger/events/manage_events.html", {"events": events})


@login_required
@permission_required("ledger.event_admin_access")
def create_event(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("ledger:event_admin")
    else:
        form = EventForm()
    return render(request, "ledger/events/create_event.html", {"form": form})


@login_required
@permission_required("ledger.event_admin_access")
def edit_event(request, event_id):
    event = get_object_or_404(Events, pk=event_id)
    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect("ledger:event_admin")
    else:
        event.date_start = (
            event.date_start.strftime("%Y-%m-%dT%H:%M") if event.date_start else None
        )
        event.date_end = (
            event.date_end.strftime("%Y-%m-%dT%H:%M") if event.date_end else None
        )

        form = EventForm(instance=event)
    return render(
        request, "ledger/events/edit_event.html", {"form": form, "event": event}
    )


@login_required
@permission_required("ledger.event_admin_access")
def delete_event(request, event_id):
    event = get_object_or_404(Events, pk=event_id)
    if request.method == "POST":
        event.delete()
        return redirect("ledger:event_admin")
    return render(request, "ledger/events/delete_event.html", {"event": event})


# pylint: disable=unused-argument
def load_events(request):
    events = Events.objects.all()
    formatted_events = []
    for event in events:
        formatted_description = escape(event.description).replace("\n", "<br>")
        formatted_events.append(
            {
                "id": event.id,
                "title": event.title,
                "date_start": event.date_start,
                "date_end": event.date_end,
                "description": formatted_description,
                "char_ledger": event.char_ledger,
                "location": event.location,
                "upcoming": event.date_end >= timezone.now(),
            }
        )

    return JsonResponse(formatted_events, safe=False)
