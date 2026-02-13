from django.apps import AppConfig


class DevicesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.devices"
    verbose_name = "Устройства Zigbee"

    def ready(self):
        """Инициализация приложения"""
        import apps.devices.signals  # noqa
