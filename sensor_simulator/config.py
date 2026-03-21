import os
from dataclasses import dataclass
from typing import List


@dataclass
class SimulatorConfig:
    """Конфигурация симулятора датчиков"""

    mqtt_host: str
    mqtt_port: int
    num_devices: int
    update_interval: int
    topic_prefix: str
    device_types: List[str]  # список типов устройств для симуляции

    @classmethod
    def from_env(cls) -> "SimulatorConfig":
        """Создание конфигурации из переменных окружения"""
        # Парсим список типов устройств из строки, разделённой запятыми
        types_str = os.getenv(
            "SIMULATOR_DEVICE_TYPES", "temperature,motion,switch,water,switch_module"
        )
        device_types = [t.strip() for t in types_str.split(",") if t.strip()]

        return cls(
            mqtt_host=os.getenv("MQTT_BROKER_HOST", "mosquitto"),
            mqtt_port=int(os.getenv("MQTT_BROKER_PORT", "1883")),
            num_devices=int(os.getenv("SIMULATOR_NUM_DEVICES", "5")),
            update_interval=int(os.getenv("SIMULATOR_UPDATE_INTERVAL", "30")),
            topic_prefix=os.getenv("SIMULATOR_MQTT_TOPIC_PREFIX", "zigbee2mqtt"),
            device_types=device_types,
        )
