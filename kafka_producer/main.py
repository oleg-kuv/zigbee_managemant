"""
Универсальный Kafka Producer для Zigbee системы.
Принимает данные из MQTT (от симулятора или Zigbee2MQTT) и отправляет в Kafka.
Работает и в dev, и в production окружениях.
"""

import json
import logging
import signal
import socket
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt
from confluent_kafka import Producer

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class KafkaProducerConfig:
    """Конфигурация Kafka Producer"""

    mqtt_host: str
    mqtt_port: int
    mqtt_topic: str
    kafka_bootstrap_servers: str
    kafka_topic: str
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None

    @classmethod
    def from_env(cls) -> "KafkaProducerConfig":
        """Создание конфигурации из переменных окружения"""
        import os

        return cls(
            mqtt_host=os.getenv("MQTT_BROKER_HOST", "mosquitto"),
            mqtt_port=int(os.getenv("MQTT_BROKER_PORT", "1883")),
            mqtt_topic=os.getenv("MQTT_ZIGBEE2MQTT_TOPIC", "zigbee2mqtt/#"),
            kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            kafka_topic=os.getenv("KAFKA_SENSOR_RAW_TOPIC", "sensor-raw"),
            mqtt_username=os.getenv("MQTT_USERNAME"),
            mqtt_password=os.getenv("MQTT_PASSWORD"),
        )


class MQTTKafkaBridge:
    """Мост между MQTT и Kafka"""

    def __init__(self, config: KafkaProducerConfig):
        self.config = config
        self.running = False
        self.message_counter = 0
        self.last_log_time = time.time()

        # Инициализация Kafka Producer
        self._init_kafka_producer()

        # Инициализация MQTT Client
        self._init_mqtt_client()

        # Обработка сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _init_kafka_producer(self):
        """Инициализация Kafka Producer"""
        kafka_conf = {
            "bootstrap.servers": self.config.kafka_bootstrap_servers,
            "client.id": socket.gethostname(),
            "acks": "all",  # Гарантированная доставка
            "retries": 5,
            "retry.backoff.ms": 1000,
            "compression.type": "snappy",
            "queue.buffering.max.messages": 100000,
            "queue.buffering.max.ms": 1000,
            "batch.num.messages": 10000,
        }

        self.kafka_producer = Producer(kafka_conf)
        logger.info(
            f"Kafka Producer initialized for {self.config.kafka_bootstrap_servers}"
        )

    def _init_mqtt_client(self):
        """Инициализация MQTT Client"""
        self.mqtt_client = mqtt.Client(
            client_id=f"kafka_producer_{int(time.time())}",
            protocol=mqtt.MQTTv311,
            clean_session=True,
        )

        # Настройка аутентификации если есть
        if self.config.mqtt_username and self.config.mqtt_password:
            self.mqtt_client.username_pw_set(
                self.config.mqtt_username, self.config.mqtt_password
            )

        # Callback функции
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
        self.mqtt_client.on_message = self._on_mqtt_message
        self.mqtt_client.on_log = self._on_mqtt_log

        # LWT (Last Will and Testament)
        self.mqtt_client.will_set(
            f"{self.config.mqtt_topic.split('/')[0]}/bridge/state",
            "offline",
            qos=1,
            retain=True,
        )

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback при подключении к MQTT брокеру"""
        if rc == 0:
            logger.info(
                f"✓ Connected to MQTT broker at {self.config.mqtt_host}:{self.config.mqtt_port}"
            )

            # Подписываемся на топик
            client.subscribe(self.config.mqtt_topic, qos=1)
            logger.info(f"✓ Subscribed to MQTT topic: {self.config.mqtt_topic}")

            # Публикуем статус онлайн
            client.publish(
                f"{self.config.mqtt_topic.split('/')[0]}/bridge/state",
                "online",
                qos=1,
                retain=True,
            )
        else:
            error_messages = {
                1: "Incorrect protocol version",
                2: "Invalid client identifier",
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized",
            }
            error_msg = error_messages.get(rc, f"Unknown error code: {rc}")
            logger.error(f"✗ MQTT connection failed: {error_msg}")

    def _on_mqtt_disconnect(self, client, userdata, rc):
        """Callback при отключении от MQTT брокера"""
        if rc != 0:
            logger.warning(f"✗ MQTT disconnected unexpectedly (code: {rc})")
            # Пытаемся переподключиться через 5 секунд
            time.sleep(5)
            try:
                client.reconnect()
            except Exception as e:
                logger.error(f"Failed to reconnect to MQTT: {e}")

    def _on_mqtt_message(self, client, userdata, msg):
        """Callback при получении сообщения из MQTT"""
        # Пропускаем bridge топики
        if "bridge" in msg.topic:
            logger.debug(f"Skipping bridge topic: {msg.topic}")
            return

        self.message_counter += 1

        try:
            # Парсим JSON сообщение
            payload = json.loads(msg.payload.decode("utf-8"))

            # Обогащаем данные метаданными
            enriched_message = self._enrich_message(msg.topic, payload)

            # Отправляем в Kafka
            self._send_to_kafka(enriched_message)

            # Логируем статистику каждые 100 сообщений или каждые 30 секунд
            current_time = time.time()
            if (
                self.message_counter % 100 == 0
                or current_time - self.last_log_time > 30
            ):
                logger.info(
                    f"Processed {self.message_counter} messages (last: {msg.topic})"
                )
                self.last_log_time = current_time

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from MQTT message: {e}")
            logger.debug(f"Raw message: {msg.payload}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}", exc_info=True)

    def _on_mqtt_log(self, client, userdata, level, buf):
        """Callback для логов MQTT (только для отладки)"""
        if level == mqtt.MQTT_LOG_DEBUG:
            logger.debug(f"MQTT: {buf}")
        elif level == mqtt.MQTT_LOG_INFO:
            logger.info(f"MQTT: {buf}")
        elif level == mqtt.MQTT_LOG_NOTICE:
            logger.info(f"MQTT: {buf}")
        elif level == mqtt.MQTT_LOG_WARNING:
            logger.warning(f"MQTT: {buf}")
        elif level == mqtt.MQTT_LOG_ERR:
            logger.error(f"MQTT: {buf}")

    def _enrich_message(
        self, mqtt_topic: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Обогащение сообщения метаданными.
        Извлекает IEEE адрес из названия топика.
        """
        # Извлекаем IEEE адрес из топика
        # Пример топика: 'zigbee2mqtt/0xa4c138e53b478e15'
        topic_parts = mqtt_topic.split("/")
        ieee_address = topic_parts[-1] if len(topic_parts) > 1 else "unknown"

        return {
            "metadata": {
                "mqtt_topic": mqtt_topic,
                "ieee_address": ieee_address,
                "received_at": time.time(),
                "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "source": self._detect_source(mqtt_topic, payload, ieee_address),
                "message_id": f"msg_{int(time.time() * 1000)}_{self.message_counter}",
            },
            "payload": payload,  # Оригинальный payload от Zigbee2MQTT
        }

    def _detect_source(
        self, mqtt_topic: str, payload: Dict[str, Any], ieee_address: str
    ) -> str:
        """
        Определение источника данных на основе полей payload.
        """
        # Проверяем, не является ли это топиком моста (bridge)
        if "bridge" in mqtt_topic:
            return "zigbee2mqtt_bridge"

        # Определяем тип устройства по полям в payload
        # 1. Температурно-влажностный датчик (ваш zg-227z)
        if "temperature" in payload and "humidity" in payload:
            return f"zigbee_sensor_temp_hum:{ieee_address}"
        # 2. Датчик движения
        elif "occupancy" in payload:
            return f"zigbee_sensor_motion:{ieee_address}"
        # 3. Выключатель/розетка
        elif "state" in payload and "power" in payload:
            return f"zigbee_switch:{ieee_address}"
        # 4. Простой выключатель
        elif "state" in payload:
            return f"zigbee_switch_simple:{ieee_address}"
        # 5. Датчик протечки
        elif "water_leak" in payload:
            return f"zigbee_sensor_water:{ieee_address}"
        # 6. Контактный датчик
        elif "contact" in payload:
            return f"zigbee_sensor_contact:{ieee_address}"
        # 7. Универсальный источник для неизвестных устройств
        else:
            return f"zigbee_device:{ieee_address}"

    def _send_to_kafka(self, message: Dict[str, Any]):
        """Отправка сообщения в Kafka"""
        try:
            # Используем топик устройства как ключ для партиционирования
            key = message["metadata"]["mqtt_topic"].encode("utf-8")
            value = json.dumps(message).encode("utf-8")

            self.kafka_producer.produce(
                topic=self.config.kafka_topic,
                key=key,
                value=value,
                callback=self._kafka_delivery_callback,
                timestamp=int(time.time() * 1000),
            )

            # Периодически flush для гарантии доставки
            if self.message_counter % 100 == 0:
                self.kafka_producer.flush(timeout=1)

        except BufferError as e:
            logger.warning(f"Kafka producer queue is full: {e}")
            # Ждем и пробуем снова
            self.kafka_producer.flush(timeout=5)
            self._send_to_kafka(message)  # Рекурсивный вызов
        except Exception as e:
            logger.error(f"Failed to send message to Kafka: {e}", exc_info=True)

    def _kafka_delivery_callback(self, err, msg):
        """Callback для подтверждения доставки в Kafka"""
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        # else:
        #     logger.debug(f"Message delivered to {msg.topic()} "
        #                  f"[partition {msg.partition()}]")

    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для graceful shutdown"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.running = False

    def _wait_for_services(self):
        """Ожидание доступности зависимых сервисов"""
        logger.info("Waiting for services to be ready...")

        # Проверка MQTT брокера
        mqtt_ready = False
        for i in range(30):  # 30 попыток по 2 секунды = 60 секунд
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((self.config.mqtt_host, self.config.mqtt_port))
                sock.close()

                if result == 0:
                    mqtt_ready = True
                    logger.info("✓ MQTT broker is ready")
                    break
                else:
                    logger.info(f"Waiting for MQTT broker... ({i + 1}/30)")
            except Exception as e:
                logger.debug(f"MQTT check error: {e}")

            time.sleep(2)

        if not mqtt_ready:
            logger.error("MQTT broker not available after 60 seconds")
            return False

        return True

    def run(self):
        """Запуск моста MQTT-Kafka"""
        logger.info("Starting MQTT-Kafka Bridge...")
        logger.info(f"Configuration: {self.config}")

        # Ожидаем готовности сервисов
        if not self._wait_for_services():
            logger.error("Services not ready, exiting...")
            return

        # Подключаемся к MQTT
        try:
            self.mqtt_client.connect(
                self.config.mqtt_host, self.config.mqtt_port, keepalive=60
            )
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return

        # Запускаем MQTT loop
        self.mqtt_client.loop_start()
        self.running = True

        logger.info("MQTT-Kafka Bridge is running. Press Ctrl+C to stop.")

        # Основной цикл
        try:
            while self.running:
                # Периодически проверяем состояние
                time.sleep(1)

                # Периодический flush Kafka producer
                if self.message_counter % 50 == 0:
                    self.kafka_producer.flush(timeout=0.1)

        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)

        finally:
            self._shutdown()

    def _shutdown(self):
        """Корректное завершение работы"""
        logger.info("Shutting down MQTT-Kafka Bridge...")

        # Останавливаем MQTT
        if hasattr(self, "mqtt_client"):
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("MQTT client disconnected")

        # Flush Kafka producer
        if hasattr(self, "kafka_producer"):
            remaining = self.kafka_producer.flush(timeout=10)
            if remaining > 0:
                logger.warning(f"{remaining} messages not delivered to Kafka")
            else:
                logger.info("All messages delivered to Kafka")

        logger.info(f"Total messages processed: {self.message_counter}")
        logger.info("MQTT-Kafka Bridge stopped")


def main():
    """Точка входа"""
    try:
        # Загружаем конфигурацию
        config = KafkaProducerConfig.from_env()

        # Создаем и запускаем мост
        bridge = MQTTKafkaBridge(config)
        bridge.run()

    except Exception as e:
        logger.error(f"Failed to start MQTT-Kafka Bridge: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
