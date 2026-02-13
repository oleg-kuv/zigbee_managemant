import logging

from apps.devices.models import DeviceConfiguration, DeviceEvent, ZigbeeDevice
from django.db.backends.signals import connection_created
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ZigbeeDevice)
def create_device_configuration(sender, instance, created, **kwargs):
    """Создать конфигурацию по умолчанию при создании устройства"""
    if created:
        DeviceConfiguration.objects.create(device=instance)
        logger.info(f"Создана конфигурация для устройства {instance.friendly_name}")


@receiver(post_save, sender=ZigbeeDevice)
def log_device_status_change(sender, instance, created, **kwargs):
    """Логировать изменения статуса устройства"""
    if created:
        DeviceEvent.objects.create(
            device=instance,
            event_type="device_joined",
            message=f"Устройство {instance.friendly_name} добавлено в систему",
            data={"ieee_address": instance.ieee_address},
        )
    else:
        # Проверяем, изменился ли статус
        try:
            old_instance = ZigbeeDevice.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                DeviceEvent.objects.create(
                    device=instance,
                    event_type="state_change",
                    message=f"Статус устройства изменен с {old_instance.status} на {instance.status}",
                    data={
                        "old_status": old_instance.status,
                        "new_status": instance.status,
                        "battery": instance.battery_level,
                    },
                )
        except ZigbeeDevice.DoesNotExist:
            pass


@receiver(pre_save, sender=ZigbeeDevice)
def check_battery_threshold(sender, instance, **kwargs):
    """Проверка порогов батареи"""
    if instance.battery_level is not None:
        try:
            old_instance = ZigbeeDevice.objects.get(pk=instance.pk)
            if old_instance.battery_level != instance.battery_level:
                # Проверяем, упала ли батарея ниже порога
                if instance.battery_level < 10 and old_instance.battery_level >= 10:
                    DeviceEvent.objects.create(
                        device=instance,
                        event_type="battery_low",
                        severity="warning",
                        message=f"Низкий заряд батареи: {instance.battery_level}%",
                        data={"battery_level": instance.battery_level},
                    )
        except ZigbeeDevice.DoesNotExist:
            pass


@receiver(connection_created)
def start_mqtt_client(sender, connection, **kwargs):
    """
    Запуск MQTT клиента после подключения к базе данных.
    Запускается только один раз при старте приложения.
    """
    from .mqtt_client import mqtt_client

    # Проверяем, не запущен ли уже клиент
    if not hasattr(connection, "_mqtt_client_started"):
        try:
            mqtt_client.start()
            logger.info("MQTT client startup scheduled")
            connection._mqtt_client_started = True
        except Exception as e:
            logger.error(f"Failed to start MQTT client: {e}")
