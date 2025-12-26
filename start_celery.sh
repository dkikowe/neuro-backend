#!/bin/bash
# Скрипт для запуска Celery worker

cd "$(dirname "$0")"
source .venv/bin/activate

echo "🚀 Запуск Celery worker..."
celery -A app.workers.celery_app worker --loglevel=info


