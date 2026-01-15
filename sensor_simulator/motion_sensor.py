import random
import time
from typing import Any, Dict

from device_base import ZigbeeDevice


class MotionSensor(ZigbeeDevice):
    """Симулятор датчика движения"""

    def __init__(self, ieee_address: str, friendly_name: str, location: str):
        super().__init__(ieee_address, friendly_name)
        self.location = location
        self.last_motion = time.time()
        self.motion_detected = False
        self.illuminance = random.uniform(10, 500)

    def generate_data(self) -> Dict[str, Any]:
        """Генерация данных датчика движения"""
        current_time = time.time()

        # Движение происходит случайно, чаще днем
        hour = time.localtime().tm_hour
        motion_probability = 0.1 if 6 <= hour <= 22 else 0.02

        # Обновление состояния движения
        if random.random() < motion_probability:
            self.motion_detected = True
            self.last_motion = current_time
        elif current_time - self.last_motion > 60:  # Сброс через 60 секунд
            self.motion_detected = False

        # Имитация изменения освещенности
        if 6 <= hour <= 18:  # День
            self.illuminance += random.uniform(-20, 20)
            self.illuminance = min(max(self.illuminance, 100), 1000)
        else:  # Ночь
            self.illuminance += random.uniform(-5, 5)
            self.illuminance = min(max(self.illuminance, 0), 50)

        data = {
            "occupancy": self.motion_detected,
            "illuminance": round(self.illuminance, 1),
            "illuminance_lux": round(self.illuminance, 1),
            "device": {
                "friendlyName": self.friendly_name,
                "model": "RTCGQ11LM",
                "ieee_address": self.ieee_address,
            },
        }

        return data
