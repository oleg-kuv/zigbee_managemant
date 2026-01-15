-- Включение расширений
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Создание таблиц будет через Django миграции,
-- но можно добавить оптимизации для TimescaleDB
