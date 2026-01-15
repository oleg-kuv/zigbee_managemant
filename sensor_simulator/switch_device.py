import random
from typing import Any, Dict

from device_base import ZigbeeDevice


class SwitchDevice(ZigbeeDevice):
    """Симулятор управляемого устройства (розетка/выключатель)"""

    def __init__(
        self,
        ieee_address: str,
        friendly_name: str,
        location: str,
        device_type: str = "switch",
    ):
        super().__init__(ieee_address, friendly_name)
        self.location = location
        self.device_type = device_type
        self.state = "OFF"  # ON/OFF
        self.power = 0.0  # Потребляемая мощность в ваттах
        self.voltage = 220.0
        self.current = 0.0
        self.energy = 0.0  # Накопленная энергия в кВт·ч

    def generate_data(self) -> Dict[str, Any]:
        """Генерация данных управляемого устройства"""
        # Обновление потребления энергии
        if self.state == "ON":
            self.power = random.uniform(10, 100)  # 10-100 Вт
            self.current = self.power / self.voltage
            self.energy += (self.power / 1000) * (self.config.update_interval / 3600)
        else:
            self.power = 0.0
            self.current = 0.0

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

        return data

    def set_state(self, state: str):
        """Установка состояния устройства (имитация управляемого устройства)"""
        if state.upper() in ["ON", "OFF"]:
            self.state = state.upper()
            return True
        return False
