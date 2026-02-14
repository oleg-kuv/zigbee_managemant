from django.utils.translation import gettext_lazy as _

from django.apps import AppConfig


class DevicesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.timemarkers"
    verbose_name = _("Временные метки")
