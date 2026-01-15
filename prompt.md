1) Система измерения параметров среды на Zigbee
1) Архитектура: Docker-compose, Kafka, Django (ядро), Postgres/TimescaleDB, Grafana
1) Единая кодовая база, два инстанса: data-consumer (Celery) и admin-panel (Django)
1) Zigbee2MQTT как софт для координатора
1) Устройства делятся на: управляемые (актуаторы) и неуправляемые (датчики)
1) Основные сущности: PhysicalQuantity, ZigbeeDevice, SensorType, SensorCorrection, DeviceCommand, Automation
1) Управляющие команды отправляются напрямую в MQTT (минуя Kafka)
1) Координатор: Sonoff ZBDongle-P (Zigbee 3.0 USB)
1) Датчики: noname температурные датчики (Zigbee 3.0, IEEE 802.15.4)
1) Требуется сервис-симулятор датчиков, отправляющий данные в MQTT
1) Использовать UV и pyproject.toml для управления зависимостями и виртуальными окружениями
1) Использовать .env и env.template для конфигурации переменных окружения
1) Использовать Docker Compose profiles:
1) production - реальные датчики + kafka-producer (без эмулятора)
1) dev - эмулятор датчиков (без kafka-producer и реальных датчиков)
1) Использовать provisioning дашбордов в Grafana
1) Не использовать init.py файлы (или оставлять их пустыми)
1) Не использовать относительные импорты. Все импорты описывать в начале файла
