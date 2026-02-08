from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LocationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.locations'
    verbose_name = _('Местоположения')
    
    def ready(self):
        """Импортируем сигналы при запуске приложения"""
        try:
            import apps.locations.signals  # noqa: F401
        except ImportError:
            pass
