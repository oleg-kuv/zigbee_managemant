import logging
import random
import signal
import time
from typing import Any

from config import SimulatorConfig
from devices.motion_sensor import MotionSensor
from devices.switch_device import SwitchDevice
from devices.switch_module import ZigbeeSwitchModule
from devices.temperature_sensor import TemperatureSensor
from devices.water_sensor import WaterLeakSensor
from mqtt_client import MQTTClient

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SensorSimulator:
    """Основной класс симулятора датчиков"""

    def __init__(self, config: SimulatorConfig):
        self.config = config
        self.devices = []
        self.mqtt_client: MQTTClient = None
        self.running = False

        # Обработка сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Обработчик сигналов для graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def setup_mqtt(self) -> bool:
        """Настройка MQTT клиента"""
        try:
            self.mqtt_client = MQTTClient(
                host=self.config.mqtt_host,
                port=self.config.mqtt_port,
                client_id="sensor_simulator",
            )

            return self.mqtt_client.connect()

        except Exception as e:
            logger.error(f"Failed to create MQTT client: {e}")
            return False

    def create_devices(self) -> None:
        """Создание имитируемых устройств на основе выбранных типов из конфига"""
        locations = [
            "living_room",
            "bedroom",
            "kitchen",
            "bathroom",
            "balcony",
            "hallway",
            "office",
            "garage",
        ]

        # Если список типов пуст, используем все доступные
        available_types = self.config.device_types
        if not available_types:
            available_types = [
                "temperature",
                "motion",
                "switch",
                "water",
                "switch_module",
            ]

        for i in range(self.config.num_devices):
            device_type = random.choice(available_types)
            ieee_address = "0x" + "".join(random.choices("0123456789abcdef", k=16))
            location = random.choice(locations)

            if device_type == "temperature":
                friendly_name = f"temp_sensor_{i + 1:03d}"
                device = TemperatureSensor(ieee_address, friendly_name, location)
            elif device_type == "motion":
                friendly_name = f"motion_sensor_{i + 1:03d}"
                device = MotionSensor(ieee_address, friendly_name, location)
            elif device_type == "switch":
                friendly_name = f"switch_{i + 1:03d}"
                device = SwitchDevice(ieee_address, friendly_name, location)
            elif device_type == "water":
                friendly_name = f"water_sensor_{i + 1:03d}"
                device = WaterLeakSensor(ieee_address, friendly_name, location)
            elif device_type == "switch_module":
                friendly_name = f"switch_module_{i + 1:03d}"
                device = ZigbeeSwitchModule(ieee_address, friendly_name, location)
            else:
                # Если тип неизвестен, пропускаем (или можно создать базовый)
                continue

            self.devices.append(device)
            logger.info(
                f"Created {device_type} device: {friendly_name} at {location} ({ieee_address})"
            )

    def publish_device_data(self, device: Any) -> None:
        """Публикация данных устройства в MQTT"""
        try:
            payload = device.get_full_payload()
            topic = device.get_mqtt_topic(self.config.topic_prefix)

            # Имитация потери пакетов (3% вероятность)
            if random.random() > 0.03:
                success = self.mqtt_client.publish(topic, payload, qos=1)

                if success:
                    logger.debug(f"Published to {topic}")
                else:
                    logger.warning(f"Failed to publish to {topic}")

            # Убрана имитация команд для SwitchDevice, так как теперь команды приходят через подписку

        except Exception as e:
            logger.error(f"Failed to publish data for {device.friendly_name}: {e}")

    def _on_command_message(self, client, userdata, msg):
        try:
            import json

            payload = json.loads(msg.payload.decode())
            topic = msg.topic
            parts = topic.split("/")
            if len(parts) >= 2 and parts[-1] == "set":
                ieee_address = parts[-2]
            else:
                logger.warning(f"Unexpected command topic format: {topic}")
                return

            device = next(
                (d for d in self.devices if d.ieee_address == ieee_address), None
            )
            if device and hasattr(device, "handle_command"):
                if device.handle_command(payload):
                    logger.info(
                        f"Device {device.friendly_name} (IEEE: {ieee_address}) updated via command: {payload}"
                    )
                else:
                    logger.debug(f"Command received but no changes: {payload}")
            else:
                logger.warning(f"No device or handler for command topic {topic}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode command JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing command message: {e}", exc_info=True)

    def run(self) -> None:
        """Основной цикл симулятора"""
        logger.info("Starting sensor simulator...")

        if not self.setup_mqtt():
            logger.error("Failed to connect to MQTT broker. Exiting.")
            return

        self.create_devices()

        # Подписка на команды для устройств, которые их поддерживают
        for device in self.devices:
            if hasattr(device, "handle_command"):
                cmd_topic = f"{self.config.topic_prefix}/{device.ieee_address}/set"
                self.mqtt_client.subscribe(cmd_topic, self._on_command_message)
                logger.info(f"Subscribed to command topic: {cmd_topic}")

        logger.info(
            f"Simulating {len(self.devices)} devices every {self.config.update_interval} seconds"
        )
        logger.info("Press Ctrl+C to stop the simulator")

        self.running = True
        cycle_count = 0

        try:
            while self.running:
                cycle_count += 1
                logger.info(f"Starting publication cycle #{cycle_count}")

                for i, device in enumerate(self.devices):
                    self.publish_device_data(device)

                    # Небольшая задержка между устройствами
                    if i < len(self.devices) - 1:
                        time.sleep(random.uniform(0.1, 0.3))

                # Логирование каждые 10 циклов
                if cycle_count % 10 == 0:
                    logger.info(f"Completed {cycle_count} publication cycles")

                # Ожидание до следующего цикла
                for _ in range(self.config.update_interval * 10):
                    if not self.running:
                        break
                    time.sleep(0.1)

        except Exception as e:
            logger.error(f"Error in simulator main loop: {e}", exc_info=True)

        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Корректное завершение работы симулятора"""
        logger.info("Shutting down simulator...")

        if self.mqtt_client:
            self.mqtt_client.disconnect()

        logger.info("Simulator stopped.")


def main() -> None:
    """Точка входа"""
    config = SimulatorConfig.from_env()
    simulator = SensorSimulator(config)
    simulator.run()


if __name__ == "__main__":
    main()
