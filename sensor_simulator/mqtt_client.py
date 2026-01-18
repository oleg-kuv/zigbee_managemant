import json
import logging
import time
from typing import Any, Callable, Optional

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTClient:
    """Клиент для работы с MQTT брокером"""

    def __init__(self, host: str, port: int, client_id: str = "sensor_simulator"):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.client: Optional[mqtt.Client] = None
        self.connected = False

    def connect(self) -> bool:
        """Подключение к MQTT брокеру"""
        try:
            self.client = mqtt.Client(client_id=self.client_id)

            # Обработчики событий
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_publish = self._on_publish

            self.client.connect(self.host, self.port, keepalive=60)
            self.client.loop_start()

            # Ждем подключения
            for _ in range(10):
                if self.connected:
                    logger.info(f"Connected to MQTT broker at {self.host}:{self.port}")
                    return True
                time.sleep(0.5)

            logger.error("Failed to connect to MQTT broker (timeout)")
            return False

        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False

    def _on_connect(
        self, client: mqtt.Client, userdata: Any, flags: Any, rc: int
    ) -> None:
        """Обработчик подключения к MQTT"""
        if rc == 0:
            self.connected = True
        else:
            logger.error(f"MQTT connection failed with code {rc}")

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int) -> None:
        """Обработчик отключения от MQTT"""
        self.connected = False
        if rc != 0:
            logger.warning(f"MQTT disconnected unexpectedly with code {rc}")

    def _on_publish(self, client: mqtt.Client, userdata: Any, mid: int) -> None:
        """Обработчик успешной публикации"""
        logger.debug(f"Message published with mid: {mid}")

    def publish(self, topic: str, payload: dict, qos: int = 1) -> bool:
        """Публикация сообщения в MQTT"""
        if not self.connected:
            logger.warning("Not connected to MQTT broker")
            return False

        try:
            result = self.client.publish(topic, json.dumps(payload), qos=qos)
            result.wait_for_publish(timeout=2.0)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published to {topic}")
                return True
            else:
                logger.error(f"Failed to publish to {topic}: error code {result.rc}")
                return False

        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")
            return False

    def subscribe(self, topic: str, callback: Callable, qos: int = 1) -> bool:
        """Подписка на топик MQTT"""
        if not self.connected:
            logger.warning("Not connected to MQTT broker")
            return False

        try:
            self.client.subscribe(topic, qos=qos)
            self.client.message_callback_add(topic, callback)
            logger.info(f"Subscribed to topic: {topic}")
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe to {topic}: {e}")
            return False

    def disconnect(self) -> None:
        """Отключение от MQTT брокера"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")
