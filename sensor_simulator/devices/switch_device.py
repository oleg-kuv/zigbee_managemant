import random
import time
from typing import Any, Dict

from devices.device_base import ZigbeeDevice


class SwitchDevice(ZigbeeDevice):
    """Симулятор управляемого устройства (розетка/выключатель)"""

    def __init__(
        self,
        ieee_address: str,
        friendly_name: str,
        location: str,
        device_type: str = "switch",
    ):
        super().__init__(ieee_address, friendly_name, location)
        self.device_type = device_type
        self.state = random.choice(["ON", "OFF"])
        self.power = 0.0
        self.voltage = 220.0
        self.current = 0.0
        self.energy = random.uniform(0, 10.0)
        self.last_energy_update = time.time()

    def generate_data(self) -> Dict[str, Any]:
        """Генерация данных управляемого устройства"""
        current_time = time.time()

        # Обновление потребления энергии
        if self.state == "ON":
            self.power = random.uniform(10, 100)
            self.current = self.power / self.voltage

            if self.last_energy_update:
                time_diff = current_time - self.last_energy_update
                self.energy += (self.power / 1000) * (time_diff / 3600)
        else:
            self.power = 0.0
            self.current = 0.0

        self.last_energy_update = current_time

        data = {
            "state": self.state,
            "power": round(self.power, 2),
            "voltage": round(self.voltage, 1),
            "current": round(self.current, 3),
            "energy": round(self.energy, 4),
            "device": {
                "friendlyName": self.friendly_name,
                "model": "SNZB-01" if self.device_type == "switch" else "ZNCLDJ12LM",
                "ieee_address": self.ieee_address,
            },
        }

        # Медленный разряд батареи
        self.simulate_battery_drain(0.0002)

        return data

    def set_state(self, state: str) -> bool:
        """Установка состояния устройства"""
        if state.upper() in ["ON", "OFF"]:
            self.state = state.upper()
            return True
        return False
