import logging
import random
import signal
import time

from config import SimulatorConfig
from motion_sensor import MotionSensor
from mqtt_client import MQTTClient
from switch_device import SwitchDevice
from temperature_sensor import TemperatureSensor

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SensorSimulator:
    """Основной класс симулятора датчиков"""

    def __init__(self, config: SimulatorConfig):
        self.config = config
        self.devices = []
        self.mqtt_client = None
        self.running = False

        # Обработка сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def setup_mqtt(self):
        """Настройка MQTT клиента"""
        self.mqtt_client = MQTTClient(
            host=self.config.mqtt_host,
            port=self.config.mqtt_port,
            client_id="sensor_simulator",
        )

        return self.mqtt_client.connect()

    def create_devices(self):
        """Создание имитируемых устройств разных типов"""
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
        device_types = ["temperature", "motion", "switch"]

        for i in range(self.config.num_devices):
            device_type = random.choice(device_types)
            ieee_address = f"0x{random.randint(0x1000, 0xFFFF):04x}{random.randint(0x1000, 0xFFFF):04x}"
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

            # Добавляем ссылку на конфиг для switch устройств
            if hasattr(device, "config"):
                device.config = self.config

            self.devices.append(device)

            logger.info(
                f"Created {device_type} device: {friendly_name} at {location} ({ieee_address})"
            )

    def publish_device_data(self, device):
        """Публикация данных устройства в MQTT"""
        try:
            payload = device.get_full_payload()
            topic = device.get_mqtt_topic(self.config.topic_prefix)

            # Имитация потери пакетов (3% вероятность для реализма)
            if random.random() > 0.03:
                success = self.mqtt_client.publish(topic, payload, qos=1)

                if success:
                    logger.debug(f"Published to {topic}")

                    # Симуляция разряда батареи
                    if hasattr(device, "simulate_battery_drain"):
                        device.simulate_battery_drain()
                else:
                    logger.warning(f"Failed to publish to {topic}")

            # Для управляемых устройств иногда имитируем команды
            if isinstance(device, SwitchDevice) and random.random() > 0.9:
                self._simulate_switch_command(device)

        except Exception as e:
            logger.error(f"Failed to publish data for {device.friendly_name}: {e}")

    def _simulate_switch_command(self, switch_device):
        """Имитация команды для управляемого устройства"""
        # Случайное переключение состояния
        new_state = "ON" if switch_device.state == "OFF" else "OFF"

        # Публикация команды (имитация управления извне)
        command_topic = f"{self.config.topic_prefix}/{switch_device.friendly_name}/set"
        command_payload = {"state": new_state}

        if self.mqtt_client.publish(command_topic, command_payload, qos=1):
            logger.info(
                f"Simulated command for {switch_device.friendly_name}: {new_state}"
            )
            switch_device.set_state(new_state)

    def run(self):
        """Основной цикл симулятора"""
        logger.info("Starting sensor simulator...")

        if not self.setup_mqtt():
            logger.error("Failed to connect to MQTT broker. Exiting.")
            return

        self.create_devices()

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

                    # Небольшая задержка между устройствами для реализма
                    if i < len(self.devices) - 1:
                        time.sleep(random.uniform(0.1, 0.5))

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

    def shutdown(self):
        """Корректное завершение работы симулятора"""
        logger.info("Shutting down simulator...")

        if self.mqtt_client:
            self.mqtt_client.disconnect()

        logger.info("Simulator stopped.")


def main():
    """Точка входа"""
    config = SimulatorConfig.from_env()
    simulator = SensorSimulator(config)
    simulator.run()


if __name__ == "__main__":
    main()
