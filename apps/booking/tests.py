from datetime import date

from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient

from apps.booking.models import Booking, RentalSlot
from apps.booking.utils.stats import get_booking_stats
from apps.sport_center.models import SportCenter, SportField
from apps.user.models import User
from apps.utils.enum_type import RoleSystemEnum, SportTypeEnum, StatusBookingEnum, StatusFieldEnum
from django.utils import timezone


def _create_user(username, email, role):
    """
    Tạo user test đơn giản, không kiểm tra password.
    """
    return User.objects.create(
        email=email,
        username=username,
        full_name=username,
        role=role,
        is_active=True,
    )


def _seed_data():
    """
    Tạo dữ liệu test mẫu:
    - center1: owner1
      - field1: 2 booking (CONFIRMED 100, COMPLETED 120), 1 booking PENDING 50
    - center2: owner2
      - field2: 1 booking CONFIRMED 200
    """
    owner1 = _create_user("owner1", "owner1@example.com", RoleSystemEnum.OWNER.value)
    owner2 = _create_user("owner2", "owner2@example.com", RoleSystemEnum.OWNER.value)
    admin = _create_user("admin", "admin@example.com", RoleSystemEnum.ADMIN.value)

    center1 = SportCenter.objects.create(owner=owner1, name="Center 1", address="Addr 1")
    center2 = SportCenter.objects.create(owner=owner2, name="Center 2", address="Addr 2")

    field1 = SportField.objects.create(
        sport_center=center1,
        name="Field 1",
        address="Addr 1",
        sport_type=SportTypeEnum.FOOTBALL.value,
        price=100,
        status=StatusFieldEnum.ACTIVE.value,
    )
    field2 = SportField.objects.create(
        sport_center=center2,
        name="Field 2",
        address="Addr 2",
        sport_type=SportTypeEnum.FOOTBALL.value,
        price=200,
        status=StatusFieldEnum.ACTIVE.value,
    )

    slot = RentalSlot.objects.create(name="FOOTBALL", time_slot="07:00-08:00")
    today = timezone.localdate()

    Booking.objects.create(
        user=owner1,
        sport_field=field1,
        rental_slot=slot,
        price=100,
        booking_date=today,
        status=StatusBookingEnum.CONFIRMED.value,
    )
    Booking.objects.create(
        user=owner1,
        sport_field=field1,
        rental_slot=slot,
        price=120,
        booking_date=today,
        status=StatusBookingEnum.COMPLETED.value,
    )
    Booking.objects.create(
        user=owner1,
        sport_field=field1,
        rental_slot=slot,
        price=50,
        booking_date=today,
        status=StatusBookingEnum.PENDING.value,
    )
    Booking.objects.create(
        user=owner2,
        sport_field=field2,
        rental_slot=slot,
        price=200,
        booking_date=today,
        status=StatusBookingEnum.CONFIRMED.value,
    )

    return {
        "owner1": owner1,
        "owner2": owner2,
        "admin": admin,
        "field1": field1,
        "field2": field2,
        "today": today,
    }


class BookingStatsHelperTests(TestCase):
    def setUp(self):
        self.data = _seed_data()

    def test_owner_scope_and_default_statuses(self):
        stats = get_booking_stats(
            user=self.data["owner1"],
            date_from=self.data["today"],
            date_to=self.data["today"],
        )
        self.assertEqual(stats["summary"]["total_revenue"], 220.0)
        self.assertEqual(stats["summary"]["total_bookings"], 2)
        self.assertEqual(len(stats["by_center"]), 1)
        self.assertEqual(stats["by_center"][0]["center_name"], "Center 1")
        self.assertEqual(stats["top_fields"][0]["field_id"], self.data["field1"].id)

    def test_admin_sees_all_centers(self):
        stats = get_booking_stats(
            user=self.data["admin"],
            date_from=self.data["today"],
            date_to=self.data["today"],
        )
        self.assertEqual(stats["summary"]["total_revenue"], 320.0)
        self.assertEqual(stats["summary"]["total_bookings"], 3)
        self.assertEqual(len(stats["by_center"]), 2)

    def test_custom_statuses_include_pending(self):
        stats = get_booking_stats(
            user=self.data["admin"],
            date_from=self.data["today"],
            date_to=self.data["today"],
            statuses=[StatusBookingEnum.PENDING.value],
        )
        self.assertEqual(stats["summary"]["total_revenue"], 50.0)
        self.assertEqual(stats["summary"]["total_bookings"], 1)
        self.assertEqual(stats["by_status"][0]["status"], StatusBookingEnum.PENDING.value)


class BookingStatsApiTests(APITestCase):
    def setUp(self):
        self.data = _seed_data()
        self.client = APIClient()

    def test_owner_scope_on_api(self):
        self.client.force_authenticate(user=self.data["owner1"])
        url = reverse("booking_stats")
        response = self.client.get(
            url,
            {
                "date_from": self.data["today"].isoformat(),
                "date_to": self.data["today"].isoformat(),
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["summary"]["total_revenue"], 220.0)
        self.assertEqual(payload["summary"]["total_bookings"], 2)
        self.assertEqual(len(payload["by_center"]), 1)

    def test_custom_status_on_api(self):
        self.client.force_authenticate(user=self.data["admin"])
        url = reverse("booking_stats")
        response = self.client.get(
            url,
            {
                "date_from": self.data["today"].isoformat(),
                "date_to": self.data["today"].isoformat(),
                "statuses": [StatusBookingEnum.PENDING.value],
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["summary"]["total_revenue"], 50.0)
        self.assertEqual(payload["summary"]["total_bookings"], 1)
