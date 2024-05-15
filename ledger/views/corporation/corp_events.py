"""
Corporation Events
"""

from django import forms
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

# Django
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
            "description": forms.Textarea(
                attrs={"rows": 6}
            ),  # Mehrzeiliges Textfeld mit 4 Zeilen
            "char_ledger": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),  # Checkbox-Widget für BooleanField
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
    return render(request, "ledger/events/events.html", {"events": events})


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
        # Konvertieren Sie das Datum in das ISO-Format
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


def load_events(request):
    event_type = request.GET.get("type")
    page_number = request.GET.get("page")

    if type == "future":
        events = Events.objects.filter(date_end__gte=timezone.now()).order_by(
            "date_end"
        )
    else:
        events = Events.objects.filter(date_end__lt=timezone.now()).order_by(
            "-date_end"
        )

    paginator = Paginator(events, 5)
    page_obj = paginator.get_page(page_number)

    formatted_events = []
    for event in page_obj:
        # Formatieren der Beschreibung
        formatted_description = escape(event.description).replace("\n", "<br>")
        formatted_events.append((event, formatted_description))

    context = {"events": formatted_events}
    if event_type == "future":
        return render(request, "ledger/events/future_events.html", context)
    return render(request, "ledger/events/expired_events.html", context)
