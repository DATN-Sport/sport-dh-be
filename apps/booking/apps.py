from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError
from datetime import datetime, timedelta


class BookingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.booking'

    # def ready(self):
    #     from apps.booking.models import RentalSlot
    #
    #     def generate_time_slots(start_str, end_str):
    #         fmt = "%H:%M"
    #         start = datetime.strptime(start_str, fmt)
    #         end = datetime.strptime(end_str, fmt)
    #         slots = []
    #         while start + timedelta(hours=1) <= end + timedelta(hours=1):
    #             next_time = start + timedelta(hours=1)
    #             slots.append(f"{start.strftime(fmt)} - {next_time.strftime(fmt)}")
    #             start = next_time
    #             if next_time > end:
    #                 break
    #         return slots
    #
    #     try:
    #         if RentalSlot.objects.exists():
    #             return
    #
    #         for slot in generate_time_slots("06:30", "22:30"):
    #             RentalSlot.objects.get_or_create(name="FOOTBALL", time_slot=slot)
    #
    #         for slot in generate_time_slots("08:00", "20:00"):
    #             RentalSlot.objects.get_or_create(name="SPORT", time_slot=slot)
    #
    #         print("✅ RentalSlot default data created successfully.")
    #
    #     except (OperationalError, ProgrammingError):
    #         pass

