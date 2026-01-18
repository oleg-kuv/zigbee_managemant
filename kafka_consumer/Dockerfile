FROM python:3.10-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код консьюмера
COPY . .

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 consumer && chown -R consumer:consumer /app
USER consumer

CMD ["python", "-m", "main"]
