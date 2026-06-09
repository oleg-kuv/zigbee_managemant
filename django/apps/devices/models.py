import uuid

from apps.common.models import TimeStampedModel
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# Убираем старый импорт
from django.db.models import JSONField
from django.utils import timezone


class DeviceType(models.TextChoices):
    """Типы устройств Zigbee"""

    TEMPERATURE_HUMIDITY = "temperature_humidity", "Температура/Влажность"
    MOTION = "motion", "Датчик движения"
    CONTACT = "contact", "Контактный датчик"
    SWITCH = "switch", "Выключатель"
    SOCKET = "socket", "Розетка"
    LIGHT = "light", "Лампа"
    GAS = "gas", "Датчик газа"
    WATER = "water", "Датчик протечки воды"
    VIBRATION = "vibration", "Датчик вибрации"
    BUTTON = "button", "Кнопка"
    RAIN = "rain", "Датчик дождя"
    RAIN_LIGNT = "RAIN_LIGNT", "Датчик дождя и освещенности"
    VOLTAGE = "voltage", "Датчик напряжения"
    CUSTOM = "custom", "Кастомное устройство"


class DeviceStatus(models.TextChoices):
    """Статусы устройства"""

    ONLINE = "online", "В сети"
    OFFLINE = "offline", "Не в сети"
    UNKNOWN = "unknown", "Неизвестно"
    PAIRED = "paired", "Сопряжено"
    INTERVIEWING = "interviewing", "Опрашивается"
    CONFIGURING = "configuring", "Настраивается"
    ERROR = "error", "Ошибка"


class BatteryStatus(models.TextChoices):
    """Статус батареи"""

    CRITICAL = "critical", "Критический (<10%)"
    LOW = "low", "Низкий (10-30%)"
    MEDIUM = "medium", "Средний (30-70%)"
    HIGH = "high", "Высокий (70-100%)"
    UNKNOWN = "unknown", "Неизвестно"


class ZigbeeDevice(TimeStampedModel):
    """Основная модель Zigbee устройства"""

    # Основная информация
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Уникальный ID",
    )

    # Идентификаторы Zigbee
    ieee_address = models.CharField(
        max_length=23,  # Пример: 0xa4c138e53b478e15
        unique=True,
        verbose_name="IEEE адрес",
        help_text="Уникальный физический адрес устройства (16-ричный)",
    )

    nwk_address = models.CharField(
        max_length=6,  # Пример: 0x4e93
        blank=True,
        null=True,
        verbose_name="Сетевой адрес",
        help_text="Короткий сетевой адрес устройства",
    )

    # Основные поля
    friendly_name = models.CharField(
        max_length=100,
        verbose_name="Имя устройства",
        help_text="Человеко-читаемое имя устройства",
    )

    device_type = models.CharField(
        max_length=50,
        choices=DeviceType.choices,
        default=DeviceType.CUSTOM,
        verbose_name="Тип устройства",
    )

    model = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Модель устройства",
        help_text="Производитель и модель (например: Tuya ZG-227ZL)",
    )

    manufacturer = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Производитель"
    )

    # Статусы
    status = models.CharField(
        max_length=50,
        choices=DeviceStatus.choices,
        default=DeviceStatus.UNKNOWN,
        verbose_name="Статус устройства",
    )

    battery_status = models.CharField(
        max_length=50,
        choices=BatteryStatus.choices,
        default=BatteryStatus.UNKNOWN,
        verbose_name="Статус батареи",
    )

    # Метрики
    battery_level = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True,
        null=True,
        verbose_name="Уровень батареи (%)",
    )

    link_quality = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(255)],
        blank=True,
        null=True,
        verbose_name="Качество связи (LQI)",
    )

    voltage = models.FloatField(blank=True, null=True, verbose_name="Напряжение (V)")

    # Временные метки
    last_seen = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Последний контакт",
        help_text="Время последнего получения данных от устройства",
    )

    first_seen = models.DateTimeField(auto_now_add=True, verbose_name="Первый контакт")

    # Время жизни устройства
    age_days = models.IntegerField(
        default=0, editable=False, verbose_name="Возраст (дней)"
    )

    # Системные поля
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    is_simulated = models.BooleanField(default=False, verbose_name="Симулированное")

    is_permitted_to_join = models.BooleanField(
        default=False, verbose_name="Разрешено присоединение"
    )

    # Связи
    location = models.ForeignKey(
        "locations.Location",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="devices",
        verbose_name="Локация",
    )

    # Конфигурация
    configuration = JSONField(
        default=dict,
        blank=True,
        verbose_name="Конфигурация устройства",
        help_text="JSON с настройками устройства (калибровка, интервалы и т.д.)",
    )

    # Вместо ArrayField используем JSONField для хранения списка
    capabilities = JSONField(
        default=list,
        blank=True,
        verbose_name="Возможности устройства",
        help_text="Список поддерживаемых возможностей",
    )

    # Метаданные
    firmware_version = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Версия прошивки"
    )

    hardware_version = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Версия аппаратного обеспечения",
    )

    software_build_id = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="ID сборки ПО"
    )

    date_code = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Дата производства"
    )

    # Дополнительная информация
    description = models.TextField(blank=True, verbose_name="Описание")

    notes = models.TextField(blank=True, verbose_name="Заметки")

    class Meta:
        verbose_name = "Zigbee устройство"
        verbose_name_plural = "Zigbee устройства"
        ordering = ["-last_seen", "friendly_name"]
        indexes = [
            models.Index(fields=["ieee_address"]),
            models.Index(fields=["status"]),
            models.Index(fields=["device_type"]),
            models.Index(fields=["battery_status"]),
            models.Index(fields=["last_seen"]),
        ]

    def __str__(self):
        return f"{self.friendly_name} ({self.ieee_address})"

    def save(self, *args, **kwargs):
        """Переопределение сохранения для обновления статусов"""
        # Обновляем возраст устройства
        if self.first_seen:
            delta = timezone.now() - self.first_seen
            self.age_days = delta.days

        # Обновляем статус батареи
        if self.battery_level is not None:
            if self.battery_level < 10:
                self.battery_status = BatteryStatus.CRITICAL
            elif self.battery_level < 30:
                self.battery_status = BatteryStatus.LOW
            elif self.battery_level < 70:
                self.battery_status = BatteryStatus.MEDIUM
            elif self.battery_level <= 100:
                self.battery_status = BatteryStatus.HIGH
            else:
                self.battery_status = BatteryStatus.UNKNOWN

        # Обновляем статус устройства на основе last_seen
        if self.last_seen:
            time_diff = timezone.now() - self.last_seen
            if time_diff.total_seconds() > 3600:  # 1 час
                self.status = DeviceStatus.OFFLINE
            else:
                self.status = DeviceStatus.ONLINE

        super().save(*args, **kwargs)

    @property
    def is_online(self):
        """Проверка, онлайн ли устройство"""
        if not self.last_seen:
            return False
        return (timezone.now() - self.last_seen).total_seconds() < 3600

    @property
    def mqtt_topic(self):
        """Получение MQTT топика устройства"""
        return f"zigbee2mqtt/{self.friendly_name}"

    @property
    def sensor_data_available(self):
        """Есть ли данные от сенсоров"""
        from django.apps import apps

        SensorMeasurement = apps.get_model("devices", "SensorMeasurement")
        return SensorMeasurement.objects.filter(device=self).exists()

    def get_latest_measurement(self):
        """Получение последнего измерения"""
        from django.apps import apps

        SensorMeasurement = apps.get_model("devices", "SensorMeasurement")
        return (
            SensorMeasurement.objects.filter(device=self)
            .order_by("-generated_time")
            .first()
        )

    def get_measurements_count(self, hours=24):
        """Количество измерений за последние N часов"""
        from django.apps import apps

        SensorMeasurement = apps.get_model("devices", "SensorMeasurement")
        time_threshold = timezone.now() - timezone.timedelta(hours=hours)
        return SensorMeasurement.objects.filter(
            device=self, generated_time__gte=time_threshold
        ).count()


class SensorMeasurement(models.Model):
    """Измерения сенсоров устройства"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    device = models.ForeignKey(
        ZigbeeDevice,
        on_delete=models.CASCADE,
        related_name="measurements",
        verbose_name="Устройство",
    )

    # Временные метки
    generated_time = models.DateTimeField(
        verbose_name="Время измерения на устройстве",
        help_text="Время, когда измерение было сгенерировано устройством",
    )

    receive_time = models.DateTimeField(
        auto_now_add=True, verbose_name="Время получения системой"
    )

    # Данные измерений (общие для всех типов сенсоров)
    temperature = models.FloatField(
        blank=True, null=True, verbose_name="Температура (°C)"
    )

    humidity = models.FloatField(
        blank=True,
        null=True,
        verbose_name="Влажность (%)",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    pressure = models.FloatField(blank=True, null=True, verbose_name="Давление (hPa)")

    occupancy = models.BooleanField(
        blank=True, null=True, verbose_name="Обнаружено движение"
    )

    illuminance = models.FloatField(
        blank=True, null=True, verbose_name="Освещенность (lux)"
    )

    illuminance_lux = models.FloatField(
        blank=True, null=True, verbose_name="Освещенность (lux)"
    )

    # Для управляемых устройств
    state = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Состояние",
        choices=[("ON", "Включено"), ("OFF", "Выключено")],
    )

    power = models.FloatField(blank=True, null=True, verbose_name="Мощность (W)")

    voltage_sensor = models.FloatField(
        blank=True, null=True, verbose_name="Напряжение (V)"
    )

    current = models.FloatField(blank=True, null=True, verbose_name="Ток (A)")

    energy = models.FloatField(
        blank=True, null=True, verbose_name="Потребленная энергия (kWh)"
    )

    # Метаданные измерения
    linkquality = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Качество связи",
        validators=[MinValueValidator(0), MaxValueValidator(255)],
    )

    battery = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Батарея (%)",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    # Дополнительные данные в JSON
    raw_data = JSONField(
        default=dict,
        blank=True,
        verbose_name="Исходные данные",
        help_text="Полные данные в формате JSON",
    )

    # Флаги
    is_processed = models.BooleanField(default=False, verbose_name="Обработано")

    has_anomaly = models.BooleanField(default=False, verbose_name="Аномалия")

    anomaly_score = models.FloatField(default=0.0, verbose_name="Оценка аномальности")

    class Meta:
        verbose_name = "Измерение сенсора"
        verbose_name_plural = "Измерения сенсоров"
        ordering = ["-generated_time"]
        indexes = [
            models.Index(fields=["device", "generated_time"]),
            models.Index(fields=["generated_time"]),
            models.Index(fields=["temperature"]),
            models.Index(fields=["humidity"]),
            models.Index(fields=["has_anomaly"]),
        ]

    def __str__(self):
        return f"{self.device.friendly_name} - {self.generated_time}"

    @property
    def latency_ms(self):
        """Задержка между генерацией и получением (в мс)"""
        if self.generated_time and self.receive_time:
            delta = self.receive_time - self.generated_time
            return int(delta.total_seconds() * 1000)
        return None


class DeviceEvent(models.Model):
    """События устройства (присоединение, ошибки, команды)"""

    class EventType(models.TextChoices):
        DEVICE_JOINED = "device_joined", "Устройство присоединилось"
        DEVICE_ANNOUNCE = "device_announce", "Устройство объявилось"
        DEVICE_INTERVIEW = "device_interview", "Опрос устройства"
        DEVICE_LEAVE = "device_leave", "Устройство отключилось"
        DEVICE_MESSAGE = "device_message", "Сообщение устройства"
        DEVICE_ERROR = "device_error", "Ошибка устройства"
        COMMAND_SENT = "command_sent", "Команда отправлена"
        COMMAND_RECEIVED = "command_received", "Команда получена"
        BATTERY_LOW = "battery_low", "Низкий заряд батареи"
        CONNECTION_LOST = "connection_lost", "Потеряно соединение"
        CONNECTION_RESTORED = "connection_restored", "Соединение восстановлено"
        STATE_CHANGE = "state_change", "Изменение состояния"
        ALARM = "alarm", "Тревога"

    class EventSeverity(models.TextChoices):
        INFO = "info", "Информация"
        WARNING = "warning", "Предупреждение"
        ERROR = "error", "Ошибка"
        CRITICAL = "critical", "Критическая ошибка"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    device = models.ForeignKey(
        ZigbeeDevice,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="Устройство",
    )

    event_type = models.CharField(
        max_length=50, choices=EventType.choices, verbose_name="Тип события"
    )

    severity = models.CharField(
        max_length=50,
        choices=EventSeverity.choices,
        default=EventSeverity.INFO,
        verbose_name="Важность",
    )

    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время события")

    message = models.TextField(verbose_name="Сообщение")

    data = JSONField(default=dict, blank=True, verbose_name="Данные события")

    is_resolved = models.BooleanField(default=False, verbose_name="Решено")

    resolved_at = models.DateTimeField(
        blank=True, null=True, verbose_name="Время решения"
    )

    resolved_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Решено кем",
    )

    resolution_notes = models.TextField(blank=True, verbose_name="Заметки по решению")

    class Meta:
        verbose_name = "Событие устройства"
        verbose_name_plural = "События устройств"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["device", "timestamp"]),
            models.Index(fields=["event_type"]),
            models.Index(fields=["severity"]),
            models.Index(fields=["is_resolved"]),
        ]

    def __str__(self):
        return f"{self.device.friendly_name} - {self.event_type} - {self.timestamp}"


class DeviceGroup(TimeStampedModel):
    """Группы устройств для управления"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100, verbose_name="Название группы")

    description = models.TextField(blank=True, verbose_name="Описание")

    devices = models.ManyToManyField(
        ZigbeeDevice, related_name="groups", blank=True, verbose_name="Устройства"
    )

    class Meta:
        verbose_name = "Группа устройств"
        verbose_name_plural = "Группы устройств"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def device_count(self):
        return self.devices.count()

    @property
    def online_count(self):
        return self.devices.filter(status=DeviceStatus.ONLINE).count()


class DeviceConfiguration(TimeStampedModel):
    """Конфигурация устройства"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    device = models.OneToOneField(
        ZigbeeDevice,
        on_delete=models.CASCADE,
        related_name="config",
        verbose_name="Устройство",
    )

    # Настройки опроса
    polling_interval = models.IntegerField(
        default=300,
        verbose_name="Интервал опроса (сек)",
        help_text="Интервал между опросами устройства",
    )

    report_interval = models.IntegerField(
        default=60,
        verbose_name="Интервал отчетов (сек)",
        help_text="Интервал отправки отчетов устройством",
    )

    # Калибровки
    temperature_calibration = models.FloatField(
        default=0.0,
        verbose_name="Калибровка температуры",
        help_text="Коррекция температуры в °C",
    )

    humidity_calibration = models.FloatField(
        default=0.0,
        verbose_name="Калибровка влажности",
        help_text="Коррекция влажности в %",
    )

    pressure_calibration = models.FloatField(
        default=0.0,
        verbose_name="Калибровка давления",
        help_text="Коррекция давления в hPa",
    )

    # Пороги тревог
    temperature_min = models.FloatField(
        blank=True,
        null=True,
        verbose_name="Минимальная температура",
        help_text="Нижний порог тревоги",
    )

    temperature_max = models.FloatField(
        blank=True,
        null=True,
        verbose_name="Максимальная температура",
        help_text="Верхний порог тревоги",
    )

    humidity_min = models.FloatField(
        blank=True,
        null=True,
        verbose_name="Минимальная влажность",
        help_text="Нижний порог тревоги",
    )

    humidity_max = models.FloatField(
        blank=True,
        null=True,
        verbose_name="Максимальная влажность",
        help_text="Верхний порог тревоги",
    )

    # Другие настройки
    enable_alerts = models.BooleanField(
        default=True, verbose_name="Включить уведомления"
    )

    enable_logging = models.BooleanField(
        default=True, verbose_name="Включить логирование"
    )

    retention_days = models.IntegerField(
        default=90, verbose_name="Хранение данных (дней)"
    )

    # Расширенные настройки
    advanced_config = JSONField(
        default=dict, blank=True, verbose_name="Расширенная конфигурация"
    )

    class Meta:
        verbose_name = "Конфигурация устройства"
        verbose_name_plural = "Конфигурации устройств"

    def __str__(self):
        return f"Конфигурация: {self.device.friendly_name}"


class DeviceStats(models.Model):
    """Модель для вью device_stats (только для чтения)"""

    ieee_address = models.CharField(
        primary_key=True, max_length=23, verbose_name="IEEE адрес"
    )

    measurement_count = models.BigIntegerField(verbose_name="Количество измерений")

    first_measurement = models.DateTimeField(verbose_name="Первое измерение")

    last_measurement = models.DateTimeField(verbose_name="Последнее измерение")

    avg_battery = models.FloatField(
        null=True, blank=True, verbose_name="Средний заряд батареи (%)"
    )

    avg_link_quality = models.FloatField(
        null=True, blank=True, verbose_name="Среднее качество связи"
    )

    max_latency_seconds = models.FloatField(
        null=True, blank=True, verbose_name="Максимальная задержка (сек)"
    )

    @property
    def coordinator_info(self):
        """Получение информации об устройстве из MQTT кэша"""
        from .mqtt_client import mqtt_client

        try:
            device_info = mqtt_client.get_device_info(self.ieee_address)
            return device_info or {}
        except Exception as e:
            print(f"Error getting coordinator info: {e}")
            return {}

    @property
    def friendly_name(self):
        """Имя устройства из координатора"""
        info = self.coordinator_info
        return info.get("friendly_name", self.ieee_address)

    @property
    def device_model(self):
        """Модель устройства из координатора"""
        info = self.coordinator_info
        return info.get("model_id", "Unknown")

    @property
    def manufacturer(self):
        """Производитель из координатора"""
        info = self.coordinator_info
        return info.get("manufacturer", "Unknown")

    @property
    def is_supported(self):
        """Поддерживается ли устройство координатором"""
        info = self.coordinator_info
        return info.get("supported", False)

    @property
    def interview_completed(self):
        """Завершен ли опрос устройства"""
        info = self.coordinator_info
        return info.get("interview_completed", False)

    @property
    def power_source(self):
        """Источник питания"""
        info = self.coordinator_info
        return info.get("power_source", "Unknown")

    @property
    def device_type(self):
        """Тип устройства из координатора"""
        info = self.coordinator_info
        return info.get("type", "Unknown")

    @property
    def definition(self):
        """Определение устройства (возможности)"""
        info = self.coordinator_info
        return info.get("definition", {})

    @property
    def has_coordinator_info(self):
        """Есть ли информация из координатора"""
        return bool(self.coordinator_info)

    @property
    def is_in_zigbeedevice(self):
        """
        Проверяет, существует ли устройство с данным IEEE адресом в модели ZigbeeDevice.
        """
        from .models import ZigbeeDevice

        try:
            return ZigbeeDevice.objects.filter(ieee_address=self.ieee_address).exists()
        except Exception:
            return False

    class Meta:
        managed = False  # Не управляется миграциями Django
        db_table = "device_stats"  # Имя вью в БД
        verbose_name = "Статистика устройства"
        verbose_name_plural = "Статистика устройств"
        ordering = ["-last_measurement"]

    def __str__(self):
        return f"Статистика: {self.ieee_address}"
