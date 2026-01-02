from django.apps import AppConfig


class FakeDataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.fake_data'
