import random
import time
from typing import Any, Dict

from devices.device_base import ZigbeeDevice


class WaterLeakSensor(ZigbeeDevice):
    """Симулятор датчика протечки воды (ZG-222Z)"""

    def __init__(self, ieee_address: str, friendly_name: str, location: str):
        super().__init__(ieee_address, friendly_name, location)
        self.water_leak = False
        self.tamper = False
        self.battery_low = False
        # Время последнего события для контроля вероятности
        self.last_leak_change = time.time()
        self.last_tamper_change = time.time()

    def generate_data(self) -> Dict[str, Any]:
        current_time = time.time()

        # Имитация протечки (редко)
        if random.random() < 0.01:  # 1% вероятность за цикл
            self.water_leak = not self.water_leak
            self.last_leak_change = current_time

        # Имитация вскрытия корпуса (tamper) — ещё реже
        if random.random() < 0.005:
            self.tamper = not self.tamper
            self.last_tamper_change = current_time

        # battery_low определяется автоматически от уровня батареи
        self.battery_low = self.battery < 10

        data = {
            "water_leak": self.water_leak,
            "tamper": self.tamper,
            "battery_low": self.battery_low,
        }

        # Разряд батареи
        self.simulate_battery_drain(0.0003)

        return data
