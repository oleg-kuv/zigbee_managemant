import os
from dataclasses import dataclass


@dataclass
class SimulatorConfig:
    """Конфигурация симулятора датчиков"""

    mqtt_host: str
    mqtt_port: int
    num_devices: int
    update_interval: int
    topic_prefix: str

    @classmethod
    def from_env(cls) -> "SimulatorConfig":
        """Создание конфигурации из переменных окружения"""
        return cls(
            mqtt_host=os.getenv("MQTT_BROKER_HOST", "mosquitto"),
            mqtt_port=int(os.getenv("MQTT_BROKER_PORT", "1883")),
            num_devices=int(os.getenv("SIMULATOR_NUM_DEVICES", "5")),
            update_interval=int(os.getenv("SIMULATOR_UPDATE_INTERVAL", "30")),
            topic_prefix=os.getenv("SIMULATOR_MQTT_TOPIC_PREFIX", "zigbee2mqtt"),
        )
