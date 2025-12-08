from apps.user.serializer_container import (
    serializers,
    StatusBookingEnum,
)

from apps.booking.utils.stats import (
    DEFAULT_STATUSES,
    PRESET_TODAY,
    PRESET_WEEK,
    PRESET_MONTH,
    PRESET_QUARTER,
)


class BookingStatsQuerySerializer(serializers.Serializer):
    preset = serializers.ChoiceField(
        choices=[
            (PRESET_TODAY, PRESET_TODAY),
            (PRESET_WEEK, PRESET_WEEK),
            (PRESET_MONTH, PRESET_MONTH),
            (PRESET_QUARTER, PRESET_QUARTER),
        ],
        required=False,
        help_text="Preset thời gian. Ưu tiên nếu không truyền date_from/date_to.",
    )
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    statuses = serializers.ListField(
        child=serializers.ChoiceField(choices=StatusBookingEnum.choices()),
        required=False,
        help_text="Mặc định chỉ tính CONFIRMED/COMPLETED.",
    )
    limit_top_fields = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=50,
        default=5,
        help_text="Số sân top theo doanh thu/lượt, mặc định 5.",
    )

    def validate(self, attrs):
        preset = attrs.get("preset")
        date_from = attrs.get("date_from")
        date_to = attrs.get("date_to")

        # Nếu không truyền gì: mặc định preset = this_month
        if not preset and not date_from and not date_to:
            attrs["preset"] = PRESET_MONTH

        if date_from and not date_to:
            attrs["date_to"] = date_from
        if date_to and not date_from:
            attrs["date_from"] = date_to

        date_from = attrs.get("date_from")
        date_to = attrs.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError({"date_to": "date_to phải lớn hơn hoặc bằng date_from"})
        return attrs

    def get_statuses(self):
        return self.validated_data.get("statuses") or DEFAULT_STATUSES

    def get_limit_top_fields(self):
        return self.validated_data.get("limit_top_fields") or 5
