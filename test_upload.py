#!/usr/bin/env python3
"""
Тестовый скрипт для проверки загрузки файлов через presigned URL.

Использование:
    python test_upload.py <path_to_file> [content_type]

Пример:
    python test_upload.py image.jpg image/jpeg
    python test_upload.py document.pdf application/pdf
"""

import sys
import requests
import os

# Настройки
API_BASE_URL = "http://localhost:8080"
# Замените на ваш реальный access token
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN_HERE"


def get_presigned_url(filename: str, content_type: str = None):
    """Получить presigned URL для загрузки файла."""
    url = f"{API_BASE_URL}/upload/presign"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {"filename": filename}
    if content_type:
        data["content_type"] = content_type
    
    print(f"📤 Запрос presigned URL для файла: {filename}")
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code != 200:
        print(f"❌ Ошибка получения presigned URL: {response.status_code}")
        print(f"   Ответ: {response.text}")
        return None
    
    result = response.json()
    print(f"✅ Presigned URL получен")
    print(f"   Upload URL: {result['upload_url'][:80]}...")
    print(f"   File URL: {result['file_url']}")
    return result


def upload_file(file_path: str, upload_url: str, content_type: str = None):
    """Загрузить файл в S3 используя presigned URL."""
    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        return False
    
    print(f"\n📤 Загрузка файла: {file_path}")
    
    headers = {}
    if content_type:
        headers["Content-Type"] = content_type
    
    with open(file_path, 'rb') as f:
        response = requests.put(upload_url, headers=headers, data=f)
    
    if response.status_code == 200:
        print(f"✅ Файл успешно загружен!")
        return True
    else:
        print(f"❌ Ошибка загрузки: {response.status_code}")
        print(f"   Ответ: {response.text}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Использование: python test_upload.py <path_to_file> [content_type]")
        print("\nПримеры:")
        print("  python test_upload.py image.jpg image/jpeg")
        print("  python test_upload.py document.pdf application/pdf")
        sys.exit(1)
    
    file_path = sys.argv[1]
    filename = os.path.basename(file_path)
    content_type = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Определяем content_type автоматически, если не указан
    if not content_type:
        ext = os.path.splitext(filename)[1].lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
        }
        content_type = content_types.get(ext, 'application/octet-stream')
        print(f"📝 Автоматически определен content_type: {content_type}")
    
    # Проверяем токен
    if ACCESS_TOKEN == "YOUR_ACCESS_TOKEN_HERE":
        print("⚠️  ВНИМАНИЕ: Установите ACCESS_TOKEN в скрипте!")
        print("   Получите токен через: POST /auth/login")
        sys.exit(1)
    
    # 1. Получаем presigned URL
    result = get_presigned_url(filename, content_type)
    if not result:
        sys.exit(1)
    
    # 2. Загружаем файл
    success = upload_file(file_path, result['upload_url'], content_type)
    
    if success:
        print(f"\n✅ Готово! Файл доступен по адресу:")
        print(f"   {result['file_url']}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()


