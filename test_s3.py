import boto3
from botocore.config import Config
import os

# Заполните своими реальными значениями (не из settings, а хардкодом для проверки)
ACCESS_KEY = "ВАШ_ACCESS_KEY"
SECRET_KEY = "ВАШ_SECRET_KEY"
REGION = "ВАШ_РЕГИОН"  # например 'eu-north-1'
BUCKET = "ВАШ_БАКЕТ"

try:
    s3 = boto3.client(
        's3',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name=REGION,
        config=Config(signature_version='s3v4')
    )
    
    # Попытка просто прочитать список файлов (проверка доступа)
    s3.list_objects_v2(Bucket=BUCKET, MaxKeys=1)
    print("Успешное подключение!")
except Exception as e:
    print(f"Ошибка: {e}")

