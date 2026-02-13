"""
MQTT клиент для Django для получения данных из Zigbee2MQTT.
Работает в отдельном потоке и обновляет кэш с информацией об устройствах.
"""

import json
import logging
import threading
import time
from typing import Dict, Optional

import paho.mqtt.client as mqtt
from django.conf import settings

logger = logging.getLogger(__name__)


class Zigbee2MQTTClient:
    """Клиент для получения данных из Zigbee2MQTT"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.client = None
        self.connected = False
        self.devices_cache: Dict[str, dict] = {}
        self.cache_timestamp = 0
        self.cache_ttl = 60  # секунды
        self._initialized = True

        # Конфигурация из настроек Django
        self.mqtt_host = getattr(settings, "MQTT_BROKER_HOST", "mosquitto")
        self.mqtt_port = getattr(settings, "MQTT_BROKER_PORT", 1883)
        self.mqtt_username = getattr(settings, "MQTT_USERNAME", None)
        self.mqtt_password = getattr(settings, "MQTT_PASSWORD", None)

    def start(self):
        """Запуск MQTT клиента в отдельном потоке"""
        if self.client and self.connected:
            logger.info("MQTT client already running")
            return

        try:
            self.client = mqtt.Client(client_id=f"django_{int(time.time())}")

            if self.mqtt_username and self.mqtt_password:
                self.client.username_pw_set(self.mqtt_username, self.mqtt_password)

            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            # Подключаемся
            self.client.connect(self.mqtt_host, self.mqtt_port, 60)

            # Запускаем в отдельном потоке
            thread = threading.Thread(target=self.client.loop_forever, daemon=True)
            thread.start()

            logger.info(
                f"MQTT client started, connecting to {self.mqtt_host}:{self.mqtt_port}"
            )

        except Exception as e:
            logger.error(f"Failed to start MQTT client: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        """Обработчик подключения"""
        if rc == 0:
            self.connected = True
            logger.info("Connected to MQTT broker")

            # Подписываемся на топик bridge/devices
            client.subscribe("zigbee2mqtt/bridge/devices")
            logger.info("Subscribed to zigbee2mqtt/bridge/devices")

            # Запрашиваем актуальные данные об устройствах
            client.publish("zigbee2mqtt/bridge/request/device", json.dumps({"id": "*"}))
            logger.info("Requested device info from coordinator")

        else:
            logger.error(f"MQTT connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Обработчик отключения"""
        self.connected = False
        if rc != 0:
            logger.warning(f"MQTT disconnected unexpectedly (code: {rc})")
            # Пытаемся переподключиться через 5 секунд
            time.sleep(5)
            self.start()

    def _on_message(self, client, userdata, msg):
        """Обработчик сообщений"""
        try:
            if msg.topic == "zigbee2mqtt/bridge/devices":
                payload = json.loads(msg.payload.decode("utf-8"))

                if isinstance(payload, list):
                    # Очищаем кэш
                    self.devices_cache.clear()

                    # Заполняем кэш
                    for device in payload:
                        ieee_address = device.get("ieee_address", "").lower()
                        if (
                            ieee_address and ieee_address != "0x00124b0030dd66b3"
                        ):  # Пропускаем координатор
                            self.devices_cache[ieee_address] = device

                    self.cache_timestamp = time.time()
                    logger.info(
                        f"Updated devices cache with {len(self.devices_cache)} devices"
                    )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from MQTT: {e}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def get_device_info(self, ieee_address: str) -> Optional[dict]:
        """Получение информации об устройстве из кэша"""
        # Проверяем актуальность кэша
        if time.time() - self.cache_timestamp > self.cache_ttl:
            logger.debug("Device cache is stale, requesting update")
            self._request_device_update()

        # Ищем в кэше
        device = self.devices_cache.get(ieee_address.lower())
        if device:
            return device

        # Если не нашли, пробуем альтернативные форматы адреса
        alt_addresses = [
            ieee_address.lower(),
            f"0x{ieee_address.lower().lstrip('0x')}",
            ieee_address.upper(),
            f"0x{ieee_address.upper().lstrip('0X')}",
        ]

        for addr in alt_addresses:
            device = self.devices_cache.get(addr)
            if device:
                return device

        return None

    def _request_device_update(self):
        """Запрос обновления информации об устройствах"""
        if self.client and self.connected:
            try:
                self.client.publish(
                    "zigbee2mqtt/bridge/request/device", json.dumps({"id": "*"})
                )
                logger.debug("Requested device info update")
            except Exception as e:
                logger.error(f"Failed to request device update: {e}")

    def get_all_devices(self) -> Dict[str, dict]:
        """Получение информации о всех устройствах"""
        return self.devices_cache.copy()

    def is_cache_fresh(self) -> bool:
        """Проверка актуальности кэша"""
        return time.time() - self.cache_timestamp <= self.cache_ttl


# Глобальный экземпляр клиента
mqtt_client = Zigbee2MQTTClient()
