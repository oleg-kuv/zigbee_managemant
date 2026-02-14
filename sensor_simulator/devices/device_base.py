import random
import time
from abc import ABC, abstractmethod
from typing import Any, Dict


class ZigbeeDevice(ABC):
    """Базовый абстрактный класс для Zigbee устройств"""

    def __init__(self, ieee_address: str, friendly_name: str, location: str):
        self.ieee_address = ieee_address
        self.friendly_name = friendly_name
        self.location = location
        # Устанавливаем начальное время last_seen в прошлом
        self.last_seen = time.time() - random.randint(10, 300)
        self.battery = random.randint(80, 100)
        self.linkquality = random.randint(70, 120)
        self.last_update_time = None

    def get_base_payload(self) -> Dict[str, Any]:
        """Базовые поля для всех устройств"""
        current_time = time.time()

        # Обновляем last_seen с задержкой 1-5 секунд назад
        if not self.last_update_time or (current_time - self.last_update_time) > 1:
            self.last_seen = current_time - random.uniform(1, 5)
            self.last_update_time = current_time

        return {
            "linkquality": self.linkquality,
            "battery": self.battery,
            "voltage": round(random.uniform(2.8, 3.2), 2),
            "last_seen": int(self.last_seen * 1000),
        }

    @abstractmethod
    def generate_data(self) -> Dict[str, Any]:
        """Генерация данных конкретного устройства - должен быть переопределен"""
        pass

    def get_mqtt_topic(self, topic_prefix: str) -> str:
        """Получение MQTT топика устройства"""
        return f"{topic_prefix}/{self.ieee_address}"

    def get_full_payload(self) -> Dict[str, Any]:
        """Полный payload для отправки"""
        base = self.get_base_payload()
        specific = self.generate_data()
        return {**base, **specific}

    def simulate_battery_drain(self, drain_rate: float = 0.001) -> None:
        """Симуляция разряда батареи"""
        self.battery = max(0, self.battery - random.uniform(0, drain_rate))
        self.linkquality = max(10, self.linkquality + random.randint(-2, 2))
