FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV PYTHONPATH=/app

CMD ["celery", "-A", "worker.app.celery_app:celery_app", "worker", "-Q", "default", "-l", "info"]
