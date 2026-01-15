import random
import time
from typing import Any, Dict

from device_base import ZigbeeDevice


class TemperatureSensor(ZigbeeDevice):
    """Симулятор температурного датчика"""

    def __init__(self, ieee_address: str, friendly_name: str, location: str):
        super().__init__(ieee_address, friendly_name)
        self.location = location
        self.base_temp = random.uniform(18.0, 24.0)
        self.temp_variation = random.uniform(0.5, 2.0)
        self.humidity_base = random.uniform(40.0, 60.0)

    def generate_data(self) -> Dict[str, Any]:
        """Генерация данных температурного датчика"""
        # Имитация суточных колебаний
        hour = time.localtime().tm_hour
        daily_variation = 2.0 * abs(12 - hour) / 12

        # Случайные флуктуации
        temp_fluctuation = random.uniform(-self.temp_variation, self.temp_variation)

        temperature = round(self.base_temp - daily_variation + temp_fluctuation, 1)
        humidity = round(self.humidity_base + random.uniform(-5, 5), 1)

        # Иногда добавляем давление, если датчик его поддерживает
        pressure = None
        if random.random() > 0.7:  # 30% датчиков имеют давление
            pressure = round(random.uniform(980, 1030), 1)

        data = {
            "temperature": temperature,
            "humidity": humidity,
            "device": {
                "friendlyName": self.friendly_name,
                "model": "WSDCGQ11LM",
                "ieee_address": self.ieee_address,
            },
        }

        if pressure:
            data["pressure"] = pressure

        return data

    def simulate_battery_drain(self):
        """Симуляция разряда батареи"""
        self.battery = max(0, self.battery - random.uniform(0.01, 0.05))
        self.linkquality = max(10, self.linkquality + random.randint(-5, 5))
