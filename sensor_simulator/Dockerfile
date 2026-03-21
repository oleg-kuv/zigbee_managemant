FROM python:3.10-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt

# Копируем код симулятора
COPY . ./

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 simulator && chown -R simulator:simulator /app
USER simulator

CMD ["python", "-m", "main"]
