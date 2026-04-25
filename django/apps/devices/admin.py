import logging

from apps.devices.models import (
    DeviceConfiguration,
    DeviceEvent,
    DeviceGroup,
    DeviceStats,
    SensorMeasurement,
    ZigbeeDevice,
)
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from django import forms

from .mqtt_client import mqtt_client

logger = logging.getLogger(__name__)


class ZigbeeDeviceAdminForm(forms.ModelForm):
    device_command = forms.ChoiceField(
        choices=[("", "---"), ("OFF", _("Выключить")), ("ON", _("Включить"))],
        required=False,
        label=_("Команда устройству"),
        help_text=_(
            "Отправить команду включения/выключения (состояние не сохраняется в БД)"
        ),
    )

    class Meta:
        model = ZigbeeDevice
        fields = "__all__"


@admin.register(ZigbeeDevice)
class ZigbeeDeviceAdmin(admin.ModelAdmin):
    form = ZigbeeDeviceAdminForm
    list_display = [
        "friendly_name",
        "ieee_address",
        "device_type_display",
        "status_display",
        "battery_display",
        "online_indicator",
        "last_seen_display",
        "location_name",
        "device_actions",
    ]

    list_filter = [
        "device_type",
        "status",
        "battery_status",
        "is_active",
        "is_simulated",
        "location",
    ]

    search_fields = [
        "friendly_name",
        "ieee_address",
        "model",
        "manufacturer",
        "description",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
        "first_seen",
        "age_days",
        "mqtt_topic_link",
    ]

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "friendly_name",
                    "ieee_address",
                    "nwk_address",
                    "device_type",
                    "model",
                    "manufacturer",
                )
            },
        ),
        (
            "Статус и метрики",
            {
                "fields": (
                    "status",
                    "battery_status",
                    "battery_level",
                    "link_quality",
                    "voltage",
                    "last_seen",
                )
            },
        ),
        (
            "Конфигурация",
            {
                "fields": (
                    "location",
                    "is_active",
                    "is_simulated",
                    "is_permitted_to_join",
                    "configuration",
                    "capabilities",
                )
            },
        ),
        (
            "Информация об устройстве",
            {
                "fields": (
                    "firmware_version",
                    "hardware_version",
                    "software_build_id",
                    "date_code",
                    "description",
                    "notes",
                )
            },
        ),
        (
            "Управление",
            {
                "fields": ("device_command",),
                "classes": ("collapse",),
                "description": _(
                    "Отправка команды ON/OFF устройству без сохранения состояния в БД"
                ),
            },
        ),
        (
            "Системная информация",
            {
                "fields": (
                    "first_seen",
                    "age_days",
                    "mqtt_topic_link",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def device_type_display(self, obj):
        return obj.get_device_type_display()

    device_type_display.short_description = "Тип"

    def status_display(self, obj):
        colors = {
            "online": "green",
            "offline": "gray",
            "unknown": "orange",
            "paired": "blue",
            "interviewing": "yellow",
            "configuring": "purple",
            "error": "red",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="color: {};">{}</span>', color, obj.get_status_display()
        )

    status_display.short_description = "Статус"

    def battery_display(self, obj):
        if obj.battery_level is None:
            return "—"

        colors = {
            "critical": "red",
            "low": "orange",
            "medium": "yellow",
            "high": "green",
            "unknown": "gray",
        }
        color = colors.get(obj.battery_status, "gray")

        return format_html(
            '<span style="color: {};">{}% ({})</span>',
            color,
            obj.battery_level,
            obj.get_battery_status_display(),
        )

    battery_display.short_description = "Батарея"

    def online_indicator(self, obj):
        if obj.is_online:
            return format_html('<span style="color: green;">●</span> Онлайн')
        else:
            return format_html('<span style="color: gray;">●</span> Оффлайн')

    online_indicator.short_description = "Соединение"

    def last_seen_display(self, obj):
        if not obj.last_seen:
            return "Никогда"

        delta = timezone.now() - obj.last_seen
        if delta.days > 0:
            return f"{delta.days} д. назад"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} ч. назад"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} мин. назад"
        else:
            return "Только что"

    last_seen_display.short_description = "Последний контакт"

    def location_name(self, obj):
        return obj.location.name if obj.location else "—"

    location_name.short_description = "Локация"

    def mqtt_topic_link(self, obj):
        return format_html("<code>{}</code>", obj.mqtt_topic)

    mqtt_topic_link.short_description = "MQTT топик"

    def device_actions(self, obj):
        return format_html(
            '<a href="/admin/devices/sensormeasurement/?device__id__exact={}" '
            'class="button">Измерения</a> '
            '<a href="/admin/devices/deviceevent/?device__id__exact={}" '
            'class="button">События</a>',
            obj.id,
            obj.id,
        )

    device_actions.short_description = "Действия"

    def save_model(self, request, obj, form, change):
        # Сначала сохраняем объект (обновление метаданных)
        super().save_model(request, obj, form, change)

        # Отправляем команду устройству, если она выбрана
        command = form.cleaned_data.get("device_command")
        if command in ("ON", "OFF"):
            topic = f"{obj.mqtt_topic}/set"
            payload = {"state": command}
            logger.info(f"Sending command: topic={topic}, payload={payload}")
            try:
                if mqtt_client.publish(topic, payload):
                    self.message_user(
                        request,
                        _('Команда "%(cmd)s" отправлена устройству %(name)s')
                        % {"cmd": command, "name": obj.friendly_name},
                        level="SUCCESS",
                    )
                else:
                    self.message_user(
                        request,
                        _("MQTT клиент не подключён, команда не отправлена"),
                        level="ERROR",
                    )
            except Exception as e:
                self.message_user(
                    request,
                    _("Ошибка отправки команды: %(err)s") % {"err": str(e)},
                    level="ERROR",
                )


@admin.register(SensorMeasurement)
class SensorMeasurementAdmin(admin.ModelAdmin):
    list_display = [
        "device_name",
        "generated_time_display",
        "temperature_display",
        "humidity_display",
        "battery_display",
        "linkquality_display",
        "latency_display",
        "has_anomaly_indicator",
    ]

    list_filter = ["device", "has_anomaly", "generated_time"]

    search_fields = ["device__friendly_name", "device__ieee_address"]

    readonly_fields = ["receive_time", "latency_ms", "raw_data_preview"]

    date_hierarchy = "generated_time"

    def device_name(self, obj):
        return obj.device.friendly_name

    device_name.short_description = "Устройство"

    def generated_time_display(self, obj):
        return obj.generated_time.strftime("%Y-%m-%d %H:%M:%S")

    generated_time_display.short_description = "Время измерения"

    def temperature_display(self, obj):
        if obj.temperature is None:
            return "—"
        return f"{obj.temperature:.1f}°C"

    temperature_display.short_description = "Температура"

    def humidity_display(self, obj):
        if obj.humidity is None:
            return "—"
        return f"{obj.humidity:.0f}%"

    humidity_display.short_description = "Влажность"

    def battery_display(self, obj):
        if obj.battery is None:
            return "—"
        return f"{obj.battery}%"

    battery_display.short_description = "Батарея"

    def linkquality_display(self, obj):
        if obj.linkquality is None:
            return "—"

        if obj.linkquality > 200:
            color = "green"
        elif obj.linkquality > 100:
            color = "yellow"
        else:
            color = "red"

        return format_html('<span style="color: {};">{}</span>', color, obj.linkquality)

    linkquality_display.short_description = "Качество связи"

    def latency_display(self, obj):
        latency = obj.latency_ms
        if latency is None:
            return "—"

        if latency < 1000:
            color = "green"
        elif latency < 5000:
            color = "yellow"
        else:
            color = "red"

        return format_html('<span style="color: {};">{} мс</span>', color, latency)

    latency_display.short_description = "Задержка"

    def has_anomaly_indicator(self, obj):
        if obj.has_anomaly:
            return format_html(
                '<span style="color: red;" title="Обнаружена аномалия">⚠</span>'
            )
        return ""

    has_anomaly_indicator.short_description = "Аномалия"

    def raw_data_preview(self, obj):
        import json

        return format_html(
            '<pre style="max-height: 300px; overflow: auto;">{}</pre>',
            json.dumps(obj.raw_data, indent=2, ensure_ascii=False),
        )

    raw_data_preview.short_description = "Исходные данные (JSON)"


@admin.register(DeviceEvent)
class DeviceEventAdmin(admin.ModelAdmin):
    list_display = [
        "device_name",
        "event_type_display",
        "severity_display",
        "timestamp_display",
        "message_preview",
        "is_resolved_display",
    ]

    list_filter = ["event_type", "severity", "is_resolved", "device"]

    search_fields = ["device__friendly_name", "message", "data"]

    readonly_fields = ["timestamp"]

    date_hierarchy = "timestamp"

    def device_name(self, obj):
        return obj.device.friendly_name

    device_name.short_description = "Устройство"

    def event_type_display(self, obj):
        return obj.get_event_type_display()

    event_type_display.short_description = "Тип события"

    def severity_display(self, obj):
        colors = {
            "info": "blue",
            "warning": "orange",
            "error": "red",
            "critical": "darkred",
        }
        color = colors.get(obj.severity, "gray")
        return format_html(
            '<span style="color: {};">{}</span>', color, obj.get_severity_display()
        )

    severity_display.short_description = "Важность"

    def timestamp_display(self, obj):
        return obj.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    timestamp_display.short_description = "Время"

    def message_preview(self, obj):
        if len(obj.message) > 50:
            return f"{obj.message[:50]}..."
        return obj.message

    message_preview.short_description = "Сообщение"

    def is_resolved_display(self, obj):
        if obj.is_resolved:
            return format_html('<span style="color: green;">✓ Решено</span>')
        return format_html('<span style="color: orange;">● Активно</span>')

    is_resolved_display.short_description = "Статус"


@admin.register(DeviceGroup)
class DeviceGroupAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "device_count",
        "online_count",
        "description_preview",
        "created_at_display",
    ]

    search_fields = ["name", "description"]

    filter_horizontal = ["devices"]

    def device_count(self, obj):
        return obj.device_count

    device_count.short_description = "Устройств"

    def online_count(self, obj):
        return obj.online_count

    online_count.short_description = "Онлайн"

    def description_preview(self, obj):
        if obj.description and len(obj.description) > 50:
            return f"{obj.description[:50]}..."
        return obj.description or "—"

    description_preview.short_description = "Описание"

    def created_at_display(self, obj):
        return obj.created_at.strftime("%Y-%m-%d")

    created_at_display.short_description = "Создана"


@admin.register(DeviceConfiguration)
class DeviceConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        "device_name",
        "polling_interval",
        "report_interval",
        "enable_alerts",
        "retention_days",
    ]

    list_filter = ["enable_alerts"]

    search_fields = ["device__friendly_name"]

    def device_name(self, obj):
        return obj.device.friendly_name

    device_name.short_description = "Устройство"


@admin.register(DeviceStats)
class DeviceStatsAdmin(admin.ModelAdmin):
    list_display = [
        "ieee_address_display",
        "in_zigbeedevice_display",
        "friendly_name_display",
        "device_model_display",
        "manufacturer_display",
        "device_type_display",
        "is_supported_display",
        "interview_status_display",
        "measurement_count",
        "last_measurement",
        "avg_battery",
        "avg_link_quality",
        "cache_status",
    ]

    search_fields = [
        "ieee_address",
    ]

    readonly_fields = [
        "ieee_address",
        "measurement_count",
        "first_measurement",
        "last_measurement",
        "avg_battery",
        "avg_link_quality",
        "max_latency_seconds",
        "coordinator_info_display",
        "definition_display",
        "in_zigbeedevice_display",
    ]

    def in_zigbeedevice_display(self, obj):
        """
        Отображает, зарегистрировано ли устройство в модели ZigbeeDevice.
        """
        if obj.is_in_zigbeedevice:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ В системе</span>'
            )
        else:
            return format_html(
                '<span style="color: gray;">✗ Не зарегистрировано</span>'
                ' <a href="/admin/devices/zigbeedevice/add/?ieee_address={}" '
                'style="margin-left: 8px; background: #79aec8; padding: 2px 6px; '
                'border-radius: 4px; color: white; text-decoration: none;">'
                "Добавить</a>",
                obj.ieee_address,
            )

    in_zigbeedevice_display.short_description = "Статус в Django"
    in_zigbeedevice_display.allow_tags = True

    def ieee_address_display(self, obj):
        """Отображение IEEE адреса с иконкой кэша"""
        if obj.has_coordinator_info:
            return format_html(
                '<span title="Информация из координатора доступна">✓ {}</span>',
                obj.ieee_address,
            )
        return format_html(
            '<span style="color: gray;" title="Информация из координатора отсутствует">● {}</span>',
            obj.ieee_address,
        )

    ieee_address_display.short_description = "IEEE Адрес"
    ieee_address_display.admin_order_field = "ieee_address"

    def friendly_name_display(self, obj):
        """Отображение имени устройства"""
        friendly_name = obj.friendly_name
        if friendly_name != obj.ieee_address:
            return friendly_name
        return "—"

    friendly_name_display.short_description = "Имя устройства"

    def device_model_display(self, obj):
        """Отображение модели устройства"""
        model = obj.device_model
        if model and model != "Unknown":
            return model
        return "—"

    device_model_display.short_description = "Модель"

    def manufacturer_display(self, obj):
        """Отображение производителя"""
        manufacturer = obj.manufacturer
        if manufacturer and manufacturer != "Unknown":
            return manufacturer
        return "—"

    manufacturer_display.short_description = "Производитель"

    def device_type_display(self, obj):
        """Отображение типа устройства"""
        device_type = obj.device_type
        if device_type and device_type != "Unknown":
            return device_type
        return "—"

    device_type_display.short_description = "Тип"

    def is_supported_display(self, obj):
        """Индикатор поддержки устройства"""
        if obj.is_supported:
            return format_html('<span style="color: green;">✓ Поддерживается</span>')
        return format_html('<span style="color: orange;">⚠ Не поддерживается</span>')

    is_supported_display.short_description = "Поддержка"

    def interview_status_display(self, obj):
        """Статус опроса устройства"""
        if obj.interview_completed:
            return format_html('<span style="color: green;">✓ Завершен</span>')
        return format_html('<span style="color: orange;">⏳ В процессе</span>')

    interview_status_display.short_description = "Опрос"

    def cache_status(self, obj):
        """Статус кэша"""
        from apps.devices.mqtt_client import mqtt_client

        if mqtt_client.is_cache_fresh():
            return format_html('<span style="color: green;">Актуальный</span>')
        return format_html('<span style="color: orange;">Устаревший</span>')

    cache_status.short_description = "Кэш"

    def coordinator_info_display(self, obj):
        """Отображение полной информации из координатора"""
        import json

        info = obj.coordinator_info
        if info:
            return format_html(
                '<pre style="max-height: 300px; overflow: auto;">{}</pre>',
                json.dumps(info, indent=2, ensure_ascii=False),
            )
        return "Информация отсутствует. MQTT клиент может быть не запущен."

    coordinator_info_display.short_description = "Информация из координатора"

    def definition_display(self, obj):
        """Отображение определения устройства"""
        import json

        definition = obj.definition
        if definition:
            return format_html(
                '<pre style="max-height: 300px; overflow: auto;">{}</pre>',
                json.dumps(definition, indent=2, ensure_ascii=False),
            )
        return "Определение отсутствует"

    definition_display.short_description = "Определение устройства"

    def changelist_view(self, request, extra_context=None):
        """Добавляем кнопку для обновления информации"""
        from apps.devices.mqtt_client import mqtt_client

        # Обновляем информацию при загрузке страницы, если кэш устарел
        if not mqtt_client.is_cache_fresh():
            mqtt_client._request_device_update()

        return super().changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
