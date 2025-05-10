FROM python:3.11-slim

# Установите необходимые зависимости
RUN apt-get update && apt-get install -y libpq-dev

# Установите рабочую директорию
WORKDIR /run

# Скопируйте requirements.txt
COPY requirements.txt .

# Установите Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Скопируйте остальные файлы приложения
COPY . .

## Команда для запуска приложения
#CMD ["python", "app.py"]
