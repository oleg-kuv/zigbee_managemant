FROM python:3.10-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt

# Копируем код продюсера
COPY . ./

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 producer && chown -R producer:producer /app
USER producer

CMD ["python", "-m", "main"]
