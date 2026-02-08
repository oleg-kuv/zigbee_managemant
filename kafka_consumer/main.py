"""
Kafka Consumer для обработки данных Zigbee датчиков и сохранения в TimescaleDB.
Обрабатывает новый формат сообщений: {"metadata": {...}, "payload": {...}}
"""

import json
import logging
import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from confluent_kafka import Consumer, KafkaError
from psycopg_pool import ConnectionPool

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


@dataclass
class ConsumerConfig:
    """Конфигурация Kafka Consumer"""

    kafka_bootstrap_servers: str
    kafka_topic: str
    kafka_group_id: str
    postgres_dsn: str
    batch_size: int
    batch_timeout: float

    @classmethod
    def from_env(cls) -> "ConsumerConfig":
        """Создание конфигурации из переменных окружения"""
        import os

        return cls(
            kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            kafka_topic=os.getenv("KAFKA_SENSOR_RAW_TOPIC", "sensor-raw"),
            kafka_group_id=os.getenv(
                "KAFKA_CONSUMER_GROUP_ID", "sensor-consumer-group"
            ),
            postgres_dsn=(
                f"host={os.getenv('POSTGRES_HOST', 'postgres')} "
                f"port={os.getenv('POSTGRES_PORT', '5432')} "
                f"dbname={os.getenv('POSTGRES_DB', 'zigbee_monitoring')} "
                f"user={os.getenv('POSTGRES_USER', 'zigbeeser')} "
                f"password={os.getenv('POSTGRES_PASSWORD', 'zigbeessword')}"
            ),
            batch_size=int(os.getenv("CONSUMER_BATCH_SIZE", "50")),
            batch_timeout=float(os.getenv("CONSUMER_BATCH_TIMEOUT", "5.0")),
        )


class SensorDataProcessor:
    """Обработчик данных датчиков для нового формата сообщений"""

    @staticmethod
    def extract_device_info(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Извлечение информации об устройстве из METADATA (а не из payload!)"""
        # IEEE адрес теперь приходит в metadata от Producer'а
        ieee_address = metadata.get("ieee_address", "unknown")

        # Извлекаем friendly_name из mqtt_topic как запасной вариант
        mqtt_topic = metadata.get("mqtt_topic", "")
        friendly_name = mqtt_topic.split("/")[-1] if mqtt_topic else "unknown"

        return {
            "ieee_address": ieee_address,
            "friendly_name": metadata.get("friendly_name", friendly_name),
            "model": "unknown",  # В новом формате модели нет
        }

    @staticmethod
    def extract_sensor_data(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Извлечение данных измерений из PAYLOAD"""
        # payload содержит чистые данные датчика из Zigbee2MQTT
        # Очищаем от несериализуемых типов
        cleaned_data = {}
        for key, value in payload.items():
            if isinstance(value, (str, int, float, bool, type(None))):
                cleaned_data[key] = value
            else:
                # Преобразуем в строку если тип не поддерживается
                cleaned_data[key] = str(value)

        # Гарантируем наличие базовых полей
        if "battery" not in cleaned_data:
            cleaned_data["battery"] = None
        if "linkquality" not in cleaned_data:
            cleaned_data["linkquality"] = None

        return cleaned_data

    @staticmethod
    def parse_timestamp(timestamp_val: Any) -> datetime:
        """Универсальный парсинг timestamp из различных форматов"""
        try:
            if isinstance(timestamp_val, (int, float)):
                # Unix timestamp (секунды или миллисекунды)
                if timestamp_val > 1e10:  # Это миллисекунды
                    return datetime.fromtimestamp(timestamp_val / 1000, tz=timezone.utc)
                else:  # Секунды
                    return datetime.fromtimestamp(timestamp_val, tz=timezone.utc)
            elif isinstance(timestamp_val, str):
                # Пытаемся парсить ISO формат
                if "T" in timestamp_val:
                    return datetime.fromisoformat(timestamp_val.replace("Z", "+00:00"))
                # Пытаемся другие форматы
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"]:
                    try:
                        dt = datetime.strptime(timestamp_val, fmt)
                        return dt.replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue
        except Exception as e:
            logger.warning(f"Failed to parse timestamp '{timestamp_val}': {e}")

        # Возвращаем текущее время UTC как fallback
        return datetime.now(tz=timezone.utc)

    def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Обработка нового формата сообщения: {metadata: {...}, payload: {...}}"""
        try:
            # Новый формат: разделение на metadata и payload
            metadata = message.get("metadata", {})
            payload = message.get("payload", {})  # Это оригинальные данные Zigbee2MQTT

            # Извлекаем информацию об устройстве из METADATA
            device_info = self.extract_device_info(metadata)

            # Извлекаем данные измерений из PAYLOAD
            sensor_data = self.extract_sensor_data(payload)

            # Получаем временные метки из metadata
            received_at = self.parse_timestamp(metadata.get("received_at"))

            # generated_time можно взять из timestamp_iso, если нет - использовать received_at
            generated_time = self.parse_timestamp(
                metadata.get("timestamp_iso", metadata.get("received_at"))
            )

            # Если ieee_address всё ещё unknown, пробуем извлечь из friendly_name
            ieee_address = device_info["ieee_address"]
            if ieee_address == "unknown":
                # Пробуем извлечь из friendly_name (может быть IEEE адресом)
                friendly_name = device_info["friendly_name"]
                if friendly_name.startswith("0x") and len(friendly_name) == 18:
                    ieee_address = friendly_name
                    device_info["ieee_address"] = ieee_address

            return {
                "ieee_address": ieee_address,
                "generated_time": generated_time,
                "receive_time": received_at,
                "data": sensor_data,
                "metadata": {
                    "mqtt_topic": metadata.get("mqtt_topic", "unknown"),
                    "source": metadata.get("source", "unknown"),
                    "friendly_name": device_info["friendly_name"],
                },
            }

        except Exception as e:
            logger.error(f"Failed to process message: {e}", exc_info=True)
            return None


class DatabaseWriter:
    """Класс для записи данных в TimescaleDB"""

    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool = None

    def connect(self):
        """Создание пула соединений с базой данных"""
        try:
            self.pool = ConnectionPool(
                conninfo=self.dsn,
                min_size=1,
                max_size=10,
                open=False,
            )
            self.pool.open()

            # Проверяем соединение
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                logger.info("Successfully connected to TimescaleDB")

        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def disconnect(self):
        """Закрытие пула соединений"""
        if self.pool:
            self.pool.close()
            logger.info("Database connection pool closed")

    def insert_batch(self, measurements: List[Dict[str, Any]]) -> int:
        """Пакетная вставка измерений в базу данных"""
        if not measurements:
            return 0

        inserted_count = 0

        for measurement in measurements:
            try:
                with self.pool.connection() as conn:
                    with conn.cursor() as cur:
                        # Сериализуем данные в JSON
                        data_json = json.dumps(measurement["data"])

                        cur.execute(
                            """
                            INSERT INTO sensor_measurements 
                            (receive_time, generated_time, ieee_address, data)
                            VALUES (%s, %s, %s, %s::jsonb)
                            ON CONFLICT (receive_time, ieee_address, generated_time) 
                            DO UPDATE SET data = EXCLUDED.data
                            """,
                            (
                                measurement["receive_time"],
                                measurement["generated_time"],
                                measurement["ieee_address"],
                                data_json,
                            ),
                        )
                        conn.commit()
                        inserted_count += 1

            except Exception as e:
                logger.warning(
                    f"Failed to insert measurement for {measurement['ieee_address']}: {e}"
                )
                continue

        if inserted_count > 0:
            logger.info(
                f"Inserted {inserted_count} measurements from batch of {len(measurements)}"
            )

        return inserted_count


class KafkaSensorConsumer:
    """Основной класс консьюмера Kafka"""

    def __init__(self, config: ConsumerConfig):
        self.config = config
        self.running = False
        self.consumer = None
        self.processor = SensorDataProcessor()
        self.db_writer = DatabaseWriter(config.postgres_dsn)

        # Статистика
        self.messages_processed = 0
        self.messages_failed = 0
        self.batches_processed = 0

        # Обработка сигналов
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для graceful shutdown"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.running = False

    def _create_kafka_consumer(self):
        """Создание Kafka Consumer с минимальной конфигурацией"""
        consumer_config = {
            "bootstrap.servers": self.config.kafka_bootstrap_servers,
            "group.id": self.config.kafka_group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
            "session.timeout.ms": 10000,
        }

        logger.info(f"Creating Kafka Consumer with config: {consumer_config}")
        self.consumer = Consumer(consumer_config)
        logger.info(f"Kafka Consumer created for group: {self.config.kafka_group_id}")

    def _wait_for_kafka(self):
        """Ожидание доступности Kafka"""
        logger.info(f"Waiting for Kafka at {self.config.kafka_bootstrap_servers}...")

        for attempt in range(30):  # 30 попыток по 2 секунды
            try:
                # Создаем временный consumer для проверки
                temp_config = {
                    "bootstrap.servers": self.config.kafka_bootstrap_servers,
                    "group.id": f"test-group-{attempt}",
                }

                test_consumer = Consumer(temp_config)
                metadata = test_consumer.list_topics(timeout=5)
                test_consumer.close()

                logger.info(f"Connected to Kafka. Found {len(metadata.topics)} topics.")

                # Проверяем наличие топика
                if self.config.kafka_topic in metadata.topics:
                    logger.info(f"Topic '{self.config.kafka_topic}' exists.")
                    return True
                else:
                    logger.warning(
                        f"Topic '{self.config.kafka_topic}' not found. Will try to auto-create."
                    )
                    return True

            except Exception as e:
                logger.debug(f"Kafka check failed (attempt {attempt + 1}/30): {e}")
                time.sleep(2)

        logger.error("Kafka not available after 60 seconds")
        return False

    def run(self):
        """Запуск консьюмера"""
        logger.info("Starting Kafka Sensor Consumer...")
        logger.info(f"Configuration: {self.config}")

        try:
            # Подключаемся к базе данных
            logger.info("Connecting to database...")
            self.db_writer.connect()

            # Ждем доступности Kafka
            if not self._wait_for_kafka():
                logger.error("Failed to connect to Kafka. Exiting.")
                return

            # Создаем Kafka Consumer
            logger.info("Creating Kafka Consumer...")
            self._create_kafka_consumer()

            # Подписываемся на топик
            logger.info(f"Subscribing to topic: {self.config.kafka_topic}")
            self.consumer.subscribe([self.config.kafka_topic])

            self.running = True
            logger.info("Consumer is running. Press Ctrl+C to stop.")

            batch_messages = []
            batch_start_time = time.time()

            # Основной цикл обработки
            while self.running:
                try:
                    # Читаем сообщение
                    msg = self.consumer.poll(timeout=1.0)

                    if msg is None:
                        # Проверяем, не пора ли сохранить батч
                        if batch_messages and (
                            time.time() - batch_start_time > self.config.batch_timeout
                        ):
                            self._save_batch(batch_messages)
                            batch_messages = []
                            batch_start_time = time.time()
                        continue

                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            logger.debug("Reached end of partition")
                        else:
                            logger.error(f"Kafka error: {msg.error()}")
                        continue

                    try:
                        # Декодируем сообщение
                        message_data = json.loads(msg.value().decode("utf-8"))

                        # Проверяем, что это новый формат сообщения
                        if (
                            not isinstance(message_data, dict)
                            or "metadata" not in message_data
                        ):
                            logger.warning(
                                f"Unexpected message format: {type(message_data)}"
                            )
                            self.messages_failed += 1
                            continue

                        # Обрабатываем сообщение
                        processed_message = self.processor.process_message(message_data)
                        if processed_message:
                            batch_messages.append(processed_message)
                        else:
                            self.messages_failed += 1

                        # Если батч достиг размера или времени - сохраняем
                        if (
                            len(batch_messages) >= self.config.batch_size
                            or time.time() - batch_start_time
                            > self.config.batch_timeout
                        ):
                            self._save_batch(batch_messages)
                            batch_messages = []
                            batch_start_time = time.time()

                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        self.messages_failed += 1
                        logger.error(f"Failed to decode message: {e}")

                except KeyboardInterrupt:
                    logger.info("Shutdown requested by user")
                    break

                except Exception as e:
                    logger.error(f"Error in main loop: {e}", exc_info=True)
                    time.sleep(1)

        except Exception as e:
            logger.error(f"Failed to start consumer: {e}", exc_info=True)

        finally:
            # Сохраняем оставшиеся сообщения
            if batch_messages:
                self._save_batch(batch_messages)
            self.shutdown()

    def _save_batch(self, messages: List[Dict[str, Any]]):
        """Сохранение батча сообщений"""
        if not messages:
            return

        try:
            inserted_count = self.db_writer.insert_batch(messages)
            self.batches_processed += 1
            self.messages_processed += len(messages)

            logger.info(
                f"Batch #{self.batches_processed}: "
                f"received={len(messages)}, "
                f"inserted={inserted_count}"
            )

            # Логируем статистику каждые 10 пакетов
            if self.batches_processed % 10 == 0:
                logger.info(
                    f"Total statistics: "
                    f"messages={self.messages_processed}, "
                    f"failed={self.messages_failed}, "
                    f"batches={self.batches_processed}"
                )

        except Exception as e:
            logger.error(f"Failed to save batch: {e}", exc_info=True)

    def shutdown(self):
        """Корректное завершение работы"""
        logger.info("Shutting down Kafka Consumer...")

        # Закрываем Kafka Consumer
        if self.consumer:
            try:
                self.consumer.close()
                logger.info("Kafka Consumer closed")
            except Exception as e:
                logger.error(f"Error closing Kafka Consumer: {e}")

        # Закрываем соединение с базой данных
        self.db_writer.disconnect()

        # Выводим финальную статистику
        logger.info(
            f"Final statistics: "
            f"messages_processed={self.messages_processed}, "
            f"messages_failed={self.messages_failed}, "
            f"batches_processed={self.batches_processed}"
        )

        logger.info("Consumer stopped.")


def main():
    """Точка входа"""
    try:
        # Загружаем конфигурацию
        config = ConsumerConfig.from_env()

        # Создаем и запускаем консьюмер
        consumer = KafkaSensorConsumer(config)
        consumer.run()

    except Exception as e:
        logger.error(f"Failed to start consumer: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
