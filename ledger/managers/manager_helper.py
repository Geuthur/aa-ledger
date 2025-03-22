from django.db import models
from django.db.models import Case, DecimalField, F, Sum, Value, When
from django.db.models.functions import Coalesce
from django.utils import timezone


def _annotations_information(
    filter_date: timezone.datetime, type_names
) -> models.QuerySet:
    """Create the Annotations for the Queryset for Information Modal."""
    annotations = {}
    for type_name in type_names:
        annotations[f"{type_name}_total_amount"] = Coalesce(
            Sum(
                Case(
                    When(
                        **{
                            f"{type_name}__isnull": False,
                            "date__year": filter_date.year,
                        },
                        then=F(type_name),
                    )
                )
            ),
            Value(0),
            output_field=DecimalField(),
        )
        annotations[f"{type_name}_total_amount_day"] = Coalesce(
            Sum(
                Case(
                    When(
                        **{
                            f"{type_name}__isnull": False,
                            "date__year": filter_date.year,
                            "date__month": filter_date.month,
                            "date__day": filter_date.day,
                        },
                        then=F(type_name),
                    )
                )
            ),
            Value(0),
            output_field=DecimalField(),
        )
        annotations[f"{type_name}_total_amount_hour"] = Coalesce(
            Sum(
                Case(
                    When(
                        **{
                            f"{type_name}__isnull": False,
                            "date__year": filter_date.year,
                            "date__month": filter_date.month,
                            "date__day": filter_date.day,
                            "date__hour": filter_date.hour,
                        },
                        then=F(type_name),
                    )
                )
            ),
            Value(0),
            output_field=DecimalField(),
        )
    return annotations
