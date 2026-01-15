import random
import time
from typing import Any, Dict


class ZigbeeDevice:
    """Базовый класс для Zigbee устройств"""

    def __init__(self, ieee_address: str, friendly_name: str):
        self.ieee_address = ieee_address
        self.friendly_name = friendly_name
        self.last_seen = time.time()
        self.battery = random.randint(80, 100)
        self.linkquality = random.randint(70, 120)

    def get_base_payload(self) -> Dict[str, Any]:
        """Базовые поля для всех устройств"""
        return {
            "linkquality": self.linkquality,
            "battery": self.battery,
            "voltage": round(random.uniform(2.8, 3.2), 2),
            "last_seen": int(time.time() * 1000),
        }

    def generate_data(self) -> Dict[str, Any]:
        """Генерация данных конкретного устройства - должен быть переопределен"""
        raise NotImplementedError("Subclasses must implement generate_data")

    def get_mqtt_topic(self, topic_prefix: str) -> str:
        """Получение MQTT топика устройства"""
        return f"{topic_prefix}/{self.friendly_name}"

    def get_full_payload(self) -> Dict[str, Any]:
        """Полный payload для отправки"""
        base = self.get_base_payload()
        specific = self.generate_data()
        return {**base, **specific}
