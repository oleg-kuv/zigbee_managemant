CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

DROP TABLE IF EXISTS sensor_measurements CASCADE;

CREATE TABLE sensor_measurements (
    -- Время получения системой (колонка партиционирования TimescaleDB!)
    receive_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Время измерения на устройстве
    generated_time TIMESTAMPTZ NOT NULL,
    
    -- Уникальный идентификатор устройства (IEEE address)
    ieee_address TEXT NOT NULL,
    
    -- ВСЕ данные измерения (без поля device!)
    data JSONB NOT NULL DEFAULT '{}'
);

-- ===== TIMESCALEDB HYPERTABLE =====
-- Партиционируем по receive_time
SELECT create_hypertable(
    'sensor_measurements', 
    'receive_time',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '7 days',
    create_default_indexes => FALSE
);

-- ===== CONSTRAINTS =====
-- TimescaleDB ТРЕБУЕТ колонку партиционирования в уникальном constraint!
ALTER TABLE sensor_measurements 
ADD CONSTRAINT unique_device_measurement 
UNIQUE (receive_time, ieee_address, generated_time);

-- Проверки времени
ALTER TABLE sensor_measurements
ADD CONSTRAINT valid_generated_time 
CHECK (generated_time <= NOW() + INTERVAL '5 minutes');

ALTER TABLE sensor_measurements
ADD CONSTRAINT valid_receive_time 
CHECK (receive_time >= generated_time);

-- ===== INDEXES =====

-- 1. Основной индекс для запросов по времени получения
CREATE INDEX idx_sensor_receive_time ON sensor_measurements (receive_time DESC);

-- 2. Индекс для запросов по времени генерации
CREATE INDEX idx_sensor_generated_time ON sensor_measurements (generated_time DESC);

-- 3. Индекс для запросов по устройству
CREATE INDEX idx_sensor_ieee_address ON sensor_measurements (ieee_address);

-- 4. Комбинированный индекс: устройство + время генерации
CREATE INDEX idx_sensor_ieee_generated ON sensor_measurements (ieee_address, generated_time DESC);

-- 5. JSONB индекс для быстрого поиска по данным
CREATE INDEX idx_sensor_data ON sensor_measurements USING GIN (data);

-- 6. Индекс для батареи (часто используется)
CREATE INDEX idx_sensor_data_battery ON sensor_measurements 
USING GIN ((data->'battery')) WHERE data ? 'battery';

-- 7. Индекс для температуры
CREATE INDEX idx_sensor_data_temperature ON sensor_measurements 
USING GIN ((data->'temperature')) WHERE data ? 'temperature';

-- ===== TIMESCALEDB COMPRESSION =====
ALTER TABLE sensor_measurements SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'ieee_address',
    timescaledb.compress_orderby = 'receive_time DESC, generated_time DESC'
);

-- Компрессия через 30 дней
SELECT add_compression_policy('sensor_measurements', INTERVAL '30 days');

-- ===== HELPER FUNCTIONS =====
-- Исправленная функция (все параметры после DEFAULT должны иметь DEFAULT)
CREATE OR REPLACE FUNCTION insert_sensor_measurement(
    p_receive_time TIMESTAMPTZ,
    p_generated_time TIMESTAMPTZ,
    p_ieee_address TEXT,
    p_data JSONB
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO sensor_measurements (receive_time, generated_time, ieee_address, data)
    VALUES (p_receive_time, p_generated_time, p_ieee_address, p_data)
    ON CONFLICT (receive_time, ieee_address, generated_time) 
    DO UPDATE SET
        data = EXCLUDED.data;
END;
$$ LANGUAGE plpgsql;

-- Альтернативная функция с DEFAULT только в конце
CREATE OR REPLACE FUNCTION insert_sensor_measurement_simple(
    p_generated_time TIMESTAMPTZ,
    p_ieee_address TEXT,
    p_data JSONB,
    p_receive_time TIMESTAMPTZ DEFAULT NOW()
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO sensor_measurements (receive_time, generated_time, ieee_address, data)
    VALUES (p_receive_time, p_generated_time, p_ieee_address, p_data)
    ON CONFLICT (receive_time, ieee_address, generated_time) 
    DO UPDATE SET
        data = EXCLUDED.data;
END;
$$ LANGUAGE plpgsql;

-- Функция для пакетной вставки (для consumer)
CREATE OR REPLACE FUNCTION insert_sensor_batch(
    measurements JSONB[]
)
RETURNS INTEGER AS $$
DECLARE
    inserted_count INTEGER := 0;
    measurement JSONB;
BEGIN
    FOREACH measurement IN ARRAY measurements
    LOOP
        BEGIN
            INSERT INTO sensor_measurements (
                receive_time,
                generated_time,
                ieee_address,
                data
            ) VALUES (
                COALESCE(
                    (measurement->>'receive_time')::TIMESTAMPTZ,
                    NOW()
                ),
                (measurement->>'generated_time')::TIMESTAMPTZ,
                measurement->>'ieee_address',
                measurement->'data'
            )
            ON CONFLICT (receive_time, ieee_address, generated_time) 
            DO UPDATE SET
                data = EXCLUDED.data;
                
            inserted_count := inserted_count + 1;
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'Failed to insert measurement: %', SQLERRM;
        END;
    END LOOP;
    
    RETURN inserted_count;
END;
$$ LANGUAGE plpgsql;

-- ===== VIEWS =====
-- Последнее измерение каждого устройства
CREATE OR REPLACE VIEW latest_measurements AS
WITH ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY ieee_address 
               ORDER BY generated_time DESC
           ) as rn
    FROM sensor_measurements
)
SELECT 
    ieee_address,
    generated_time,
    receive_time,
    data
FROM ranked
WHERE rn = 1;

-- Статистика по устройствам
CREATE OR REPLACE VIEW device_stats AS
SELECT 
    ieee_address,
    COUNT(*) as measurement_count,
    MIN(generated_time) as first_measurement,
    MAX(generated_time) as last_measurement,
    AVG((data->>'battery')::numeric) as avg_battery,
    AVG((data->>'linkquality')::numeric) as avg_link_quality,
    MAX(receive_time - generated_time) as max_latency_seconds
FROM sensor_measurements
GROUP BY ieee_address;

-- ===== COMMENTS =====
COMMENT ON TABLE sensor_measurements IS '
TimescaleDB hypertable для хранения измерений Zigbee датчиков.
Колонки:
- receive_time: время получения системой (партиционирование)
- generated_time: время измерения на устройстве
- ieee_address: уникальный IEEE адрес устройства
- data: JSON со всеми данными (без поля device)

Уникальность: (receive_time, ieee_address, generated_time)
Компрессия: через 30 дней
';
-- ===== FUNCTIONS FOR GRAFANA =====

-- Функция для получения статистики по часам
CREATE OR REPLACE FUNCTION get_hourly_stats(
    p_hours_back integer DEFAULT 24
)
RETURNS TABLE (
    hour_start timestamptz,
    device_type text,
    measurement_count bigint
) AS $$
BEGIN
    RETURN QUERY
    WITH hourly_data AS (
        SELECT 
            date_trunc('hour', generated_time) as hour_start,
            CASE 
                WHEN data->>'temperature' IS NOT NULL THEN 'temperature'
                WHEN data->>'occupancy' IS NOT NULL THEN 'motion'
                WHEN data->>'state' IS NOT NULL THEN 'switch'
                ELSE 'other'
            END as device_type,
            COUNT(*) as measurement_count
        FROM sensor_measurements
        WHERE generated_time > NOW() - (p_hours_back || ' hours')::interval
        GROUP BY 1, 2
    )
    SELECT 
        hour_start,
        device_type,
        measurement_count
    FROM hourly_data
    ORDER BY hour_start DESC, device_type;
END;
$$ LANGUAGE plpgsql;

-- Функция для получения последних данных всех устройств
CREATE OR REPLACE FUNCTION get_latest_device_data()
RETURNS TABLE (
    ieee_address text,
    friendly_name text,
    device_type text,
    last_seen timestamptz,
    battery float,
    linkquality integer,
    temperature float,
    humidity float,
    occupancy boolean,
    state text,
    power float
) AS $$
BEGIN
    RETURN QUERY
    WITH latest AS (
        SELECT DISTINCT ON (sm.ieee_address)
            sm.ieee_address,
            sm.generated_time,
            sm.data
        FROM sensor_measurements sm
        ORDER BY sm.ieee_address, sm.generated_time DESC
    )
    SELECT 
        l.ieee_address,
        COALESCE(l.data->'device'->>'friendlyName', 'Unknown') as friendly_name,
        CASE 
            WHEN l.data->>'temperature' IS NOT NULL THEN 'temperature'
            WHEN l.data->>'occupancy' IS NOT NULL THEN 'motion'
            WHEN l.data->>'state' IS NOT NULL THEN 'switch'
            ELSE 'unknown'
        END as device_type,
        l.generated_time as last_seen,
        (l.data->>'battery')::float as battery,
        (l.data->>'linkquality')::integer as linkquality,
        (l.data->>'temperature')::float as temperature,
        (l.data->>'humidity')::float as humidity,
        (l.data->>'occupancy')::boolean as occupancy,
        l.data->>'state' as state,
        (l.data->>'power')::float as power
    FROM latest l
    ORDER BY l.generated_time DESC;
END;
$$ LANGUAGE plpgsql;

-- Представление для последних данных устройств (удобно для Grafana)
CREATE OR REPLACE VIEW latest_device_summary AS
SELECT * FROM get_latest_device_data();

-- Представление для статистики батареи
CREATE OR REPLACE VIEW battery_status AS
SELECT 
    ieee_address,
    (data->>'battery')::float as battery_level,
    generated_time,
    CASE 
        WHEN (data->>'battery')::float > 70 THEN 'high'
        WHEN (data->>'battery')::float > 30 THEN 'medium'
        ELSE 'low'
    END as battery_status
FROM sensor_measurements
WHERE data->>'battery' IS NOT NULL
  AND generated_time > NOW() - INTERVAL '24 hours'
ORDER BY generated_time DESC;

-- Функция для чистки старых данных (автоматическая)
CREATE OR REPLACE FUNCTION cleanup_old_data(p_days_to_keep integer DEFAULT 90)
RETURNS integer AS $$
DECLARE
    deleted_count integer;
BEGIN
    DELETE FROM sensor_measurements
    WHERE generated_time < NOW() - (p_days_to_keep || ' days')::interval;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
