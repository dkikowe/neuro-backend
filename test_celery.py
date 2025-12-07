#!/usr/bin/env python3
"""
Скрипт для тестирования Celery задач
"""
import sys
import time
from app.workers.celery_app import celery_app
from app.workers.tasks import generate_image_task

def test_celery_connection():
    """Проверка подключения к Celery"""
    try:
        # Проверяем доступность брокера
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            print("✅ Celery worker подключен!")
            print(f"Активных воркеров: {len(stats)}")
            for worker_name in stats:
                print(f"  - {worker_name}")
            return True
        else:
            print("❌ Celery worker не найден!")
            print("Запустите worker командой:")
            print("  celery -A app.workers.celery_app worker --loglevel=info")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к Celery: {e}")
        return False

def test_task():
    """Тестовая задача"""
    print("\n📤 Отправка тестовой задачи...")
    
    # Тестовый URL изображения (можно заменить на реальный)
    test_image_url = "https://picsum.photos/512/512"
    test_style = "anime"
    
    try:
        # Отправляем задачу
        task = generate_image_task.delay(test_image_url, test_style)
        print(f"✅ Задача отправлена! Task ID: {task.id}")
        
        # Ждем результат
        print("⏳ Ожидание результата...")
        result = task.get(timeout=180)  # 3 минуты таймаут
        
        print(f"✅ Задача выполнена успешно!")
        print(f"Результат: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка выполнения задачи: {e}")
        if hasattr(task, 'state'):
            print(f"Статус задачи: {task.state}")
            if task.state == 'FAILURE':
                print(f"Информация об ошибке: {task.info}")
        return False

if __name__ == "__main__":
    print("🔍 Проверка Celery...")
    print("=" * 50)
    
    # Проверка подключения
    if not test_celery_connection():
        sys.exit(1)
    
    # Опционально: тест задачи
    if len(sys.argv) > 1 and sys.argv[1] == "--test-task":
        test_task()
    else:
        print("\n💡 Для тестирования задачи запустите:")
        print("  python test_celery.py --test-task")

