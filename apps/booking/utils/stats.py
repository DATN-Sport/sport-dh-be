import calendar
from datetime import date, timedelta
from typing import Dict, List, Optional

from django.db.models import Count, Sum
from django.utils import timezone

from apps.booking.models import Booking
from apps.utils.enum_type import RoleSystemEnum, StatusBookingEnum

DEFAULT_STATUSES = [
    StatusBookingEnum.CONFIRMED.value,
    StatusBookingEnum.COMPLETED.value,
]

PRESET_TODAY = "today"
PRESET_WEEK = "this_week"
PRESET_MONTH = "this_month"
PRESET_QUARTER = "this_quarter"
PRESET_CHOICES = {PRESET_TODAY, PRESET_WEEK, PRESET_MONTH, PRESET_QUARTER}


def _get_quarter_date_range(today: date) -> (date, date):
    quarter_index = (today.month - 1) // 3
    start_month = quarter_index * 3 + 1
    start_date = date(today.year, start_month, 1)
    end_month = start_month + 2
    last_day = calendar.monthrange(today.year, end_month)[1]
    end_date = date(today.year, end_month, last_day)
    return start_date, end_date


def _get_date_range(preset: Optional[str], date_from: Optional[date], date_to: Optional[date]) -> (date, date):
    """
    Resolve the final date range. Priority:
    1) Explicit date_from/date_to
    2) Preset if provided
    3) Default to current month
    """
    if date_from and date_to:
        return date_from, date_to

    today = timezone.localdate()
    if preset in PRESET_CHOICES:
        if preset == PRESET_TODAY:
            return today, today
        if preset == PRESET_WEEK:
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            return start, end
        if preset == PRESET_MONTH:
            start = today.replace(day=1)
            last_day = calendar.monthrange(today.year, today.month)[1]
            end = date(today.year, today.month, last_day)
            return start, end
        if preset == PRESET_QUARTER:
            return _get_quarter_date_range(today)

    # Default: current month
    start = today.replace(day=1)
    last_day = calendar.monthrange(today.year, today.month)[1]
    end = date(today.year, today.month, last_day)
    return start, end


def _safe_number(value):
    return float(value) if value else 0.0


def _apply_owner_scope(qs, user):
    if user.role == RoleSystemEnum.OWNER.value:
        qs = qs.filter(sport_field__sport_center__owner=user)
    return qs


def get_booking_stats(
    user,
    preset: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    statuses: Optional[List[str]] = None,
    limit_top_fields: int = 5,
) -> Dict[str, object]:
    statuses = statuses or DEFAULT_STATUSES
    start_date, end_date = _get_date_range(preset, date_from, date_to)

    queryset = Booking.objects.filter(
        booking_date__gte=start_date,
        booking_date__lte=end_date,
        status__in=statuses,
    ).select_related("sport_field", "sport_field__sport_center")

    queryset = _apply_owner_scope(queryset, user)

    summary_agg = queryset.aggregate(
        total_revenue=Sum("price"),
        total_bookings=Count("id"),
    )

    by_status = list(
        queryset.values("status")
        .annotate(revenue=Sum("price"), count=Count("id"))
        .order_by("-revenue")
    )

    by_center = list(
        queryset.values("sport_field__sport_center_id", "sport_field__sport_center__name")
        .annotate(revenue=Sum("price"), count=Count("id"))
        .order_by("-revenue")
    )

    top_fields = list(
        queryset.values(
            "sport_field_id",
            "sport_field__name",
            "sport_field__sport_center_id",
            "sport_field__sport_center__name",
        )
        .annotate(revenue=Sum("price"), count=Count("id"))
        .order_by("-revenue", "-count")[:limit_top_fields]
    )

    return {
        "filters": {
            "preset": preset,
            "date_from": start_date,
            "date_to": end_date,
            "statuses": statuses,
            "limit_top_fields": limit_top_fields,
        },
        "summary": {
            "total_revenue": _safe_number(summary_agg.get("total_revenue")),
            "total_bookings": summary_agg.get("total_bookings", 0),
        },
        "by_status": by_status,
        "by_center": [
            {
                "center_id": item["sport_field__sport_center_id"],
                "center_name": item["sport_field__sport_center__name"],
                "revenue": _safe_number(item["revenue"]),
                "count": item["count"],
            }
            for item in by_center
        ],
        "top_fields": [
            {
                "field_id": item["sport_field_id"],
                "field_name": item["sport_field__name"],
                "center_id": item["sport_field__sport_center_id"],
                "center_name": item["sport_field__sport_center__name"],
                "revenue": _safe_number(item["revenue"]),
                "count": item["count"],
            }
            for item in top_fields
        ],
    }
