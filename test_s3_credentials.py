#!/usr/bin/env python3
"""
Тестовый скрипт для проверки S3 credentials.
Запустите: python test_s3_credentials.py
"""

import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(__file__))

# Используем настройки из приложения
from app.core.config import get_settings

settings = get_settings()

# Получаем credentials
access_key = settings.AWS_ACCESS_KEY_ID
secret_key = settings.AWS_SECRET_ACCESS_KEY
bucket = settings.AWS_S3_BUCKET_NAME
region = settings.AWS_S3_REGION

print("=" * 60)
print("Проверка credentials из .env файла:")
print("=" * 60)
print(f"Access Key: {access_key[:10]}..." if access_key else "Access Key: НЕ НАЙДЕН")
print(f"Secret Key length: {len(secret_key) if secret_key else 0}")
print(f"Secret Key starts: {secret_key[:5]}..." if secret_key else "Secret Key: НЕ НАЙДЕН")
print(f"Secret Key ends: ...{secret_key[-5:]}" if secret_key else "")
print(f"Secret Key contains '+': {'+' in secret_key if secret_key else False}")
print(f"Bucket: {bucket}")
print(f"Region: {region}")
print("=" * 60)

# Тест подключения к S3
if access_key and secret_key and bucket and region:
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        print("\nТестирование подключения к S3...")
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        # Пробуем получить список bucket'ов
        try:
            response = s3_client.list_buckets()
            print("✅ Подключение к S3 успешно!")
            print(f"Доступные buckets: {[b['Name'] for b in response['Buckets']]}")
            
            # Проверяем доступ к конкретному bucket
            if bucket in [b['Name'] for b in response['Buckets']]:
                print(f"✅ Bucket '{bucket}' найден и доступен")
            else:
                print(f"⚠️  Bucket '{bucket}' не найден в списке доступных")
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            print(f"❌ Ошибка при подключении к S3: {error_code} - {error_message}")
            
            if error_code == 'SignatureDoesNotMatch':
                print("\n⚠️  ПРОБЛЕМА: SignatureDoesNotMatch")
                print("Это означает, что секретный ключ неправильный или неправильно читается.")
                print("Проверьте:")
                print("1. Правильность AWS_SECRET_KEY в .env")
                print("2. Если ключ содержит '+', оберните значение в кавычки: AWS_SECRET_KEY=\"...\"")
                print("3. Что нет лишних пробелов или символов")
            
    except ImportError:
        print("❌ boto3 не установлен. Установите: pip install boto3")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
else:
    print("\n❌ Не все credentials найдены в .env файле!")
    print("Убедитесь, что в .env есть:")
    print("  AWS_ACCESS_KEY=...")
    print("  AWS_SECRET_KEY=...")
    print("  AWS_BUCKET_NAME=...")
    print("  REGION=...")

