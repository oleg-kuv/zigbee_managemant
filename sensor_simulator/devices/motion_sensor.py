import random
import time
from typing import Any, Dict

from devices.device_base import ZigbeeDevice


class MotionSensor(ZigbeeDevice):
    """Симулятор датчика движения"""

    def __init__(self, ieee_address: str, friendly_name: str, location: str):
        super().__init__(ieee_address, friendly_name, location)
        self.last_motion = time.time() - random.randint(60, 300)
        self.motion_detected = False
        self.illuminance = random.uniform(10, 500)

    def generate_data(self) -> Dict[str, Any]:
        current_time = time.time()
        hour = time.localtime().tm_hour
        motion_probability = 0.1 if 6 <= hour <= 22 else 0.02

        if random.random() < motion_probability:
            self.motion_detected = True
            self.last_motion = current_time - random.uniform(1, 3)
        elif current_time - self.last_motion > 60:
            self.motion_detected = False

        if 6 <= hour <= 18:
            self.illuminance += random.uniform(-10, 10)
            self.illuminance = min(max(self.illuminance, 100), 1000)
        else:
            self.illuminance += random.uniform(-2, 2)
            self.illuminance = min(max(self.illuminance, 0), 50)

        data = {
            "occupancy": self.motion_detected,
            "illuminance": round(self.illuminance, 1),
            "illuminance_lux": round(self.illuminance, 1),
        }

        self.simulate_battery_drain(0.001)
        return data
