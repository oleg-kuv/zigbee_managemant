import random
import time
from typing import Any, Dict

from devices.device_base import ZigbeeDevice


class TemperatureSensor(ZigbeeDevice):
    """Симулятор температурного датчика с плавными суточными колебаниями"""

    def __init__(self, ieee_address: str, friendly_name: str, location: str):
        super().__init__(ieee_address, friendly_name, location)
        # Текущая температура начинается со случайного значения в допустимом диапазоне
        self.current_temperature = random.uniform(10.0, 20.0)
        self.last_temp_update = None  # время последнего обновления температуры
        self.humidity_base = random.uniform(40.0, 60.0)

    def _get_target_temperature(self, hour: float) -> float:
        """
        Возвращает целевую температуру для данного часа (дробного).
        """
        if 0 <= hour < 7:
            return 10.0
        elif 7 <= hour < 10:
            # Линейный рост с 10 до 20 за 3 часа
            return 10.0 + (20.0 - 10.0) * ((hour - 7) / 3.0)
        elif 10 <= hour < 18:
            return 20.0
        elif 18 <= hour < 21:
            # Линейный спад с 20 до 10 за 3 часа
            return 20.0 - (20.0 - 10.0) * ((hour - 18) / 3.0)
        else:  # 21–24
            return 10.0

    def _update_temperature(self):
        """Обновляет текущую температуру с учётом времени и максимальной скорости."""
        now = time.time()
        if self.last_temp_update is None:
            self.last_temp_update = now
            return

        delta = now - self.last_temp_update  # секунд с прошлого обновления
        # Максимальное изменение за это время (1°C в час = 1/3600 °C/сек)
        max_change = delta / 3600.0

        # Получаем текущее дробное время суток
        local_time = time.localtime(now)
        hour = local_time.tm_hour + local_time.tm_min / 60.0

        target = self._get_target_temperature(hour)
        diff = target - self.current_temperature

        # Плавно двигаемся к цели, не превышая max_change
        if abs(diff) > max_change:
            change = max_change if diff > 0 else -max_change
        else:
            change = diff

        self.current_temperature += change
        self.last_temp_update = now

    def generate_data(self) -> Dict[str, Any]:
        # Обновляем температуру в соответствии со временем
        self._update_temperature()

        # Добавляем небольшой случайный шум (в пределах ±0.3°C) для реалистичности
        noise = random.uniform(-0.3, 0.3)
        temperature = round(self.current_temperature + noise, 1)

        # Генерируем влажность (оставляем как было)
        hour = time.localtime().tm_hour
        daily_variation = 2.0 * abs(12 - hour) / 12
        humidity = round(self.humidity_base + random.uniform(-2, 2), 1)

        data = {
            "temperature": temperature,
            "humidity": humidity,
            "temperature_unit": "celsius",
            "temperature_calibration": 0,
            "humidity_calibration": 0,
        }

        self.simulate_battery_drain(0.0005)
        return data
