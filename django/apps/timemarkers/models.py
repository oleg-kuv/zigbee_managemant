from apps.common.models import TimeStampedModel
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeMarker(TimeStampedModel):
    """
    Временные метки для фиксации событий (например "Начало топки", "Открыл дверь" и т.п)
    Может быть полезно при анализе данных от датчиков
    """

    name = models.CharField(
        max_length=100,
        verbose_name=_("Краткое описание"),
        help_text=_(
            "Например: 'Начал отопление', 'Дрова прогорели', 'Включил электрообогреватель'"
        ),
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Дополнительная информация о событии"),
    )

    class Meta:
        verbose_name = "Веремнная метка"
        verbose_name_plural = "Веремнные метки"

    def __str__(self):
        return f"Конфигурация: {self.name}"
