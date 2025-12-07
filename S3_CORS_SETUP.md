# Настройка CORS для S3 Bucket

Для того чтобы браузер мог загружать файлы напрямую в S3 через presigned URL, необходимо настроить CORS политику на вашем S3 bucket.

## Через AWS Console

1. Откройте AWS Console → S3 → выберите ваш bucket (`kwork-project`)
2. Перейдите на вкладку **Permissions** (Разрешения)
3. Прокрутите до секции **Cross-origin resource sharing (CORS)**
4. Нажмите **Edit** (Редактировать)
5. Вставьте следующую конфигурацию:

```json
[
    {
        "AllowedHeaders": [
            "*"
        ],
        "AllowedMethods": [
            "GET",
            "PUT",
            "POST",
            "DELETE",
            "HEAD"
        ],
        "AllowedOrigins": [
            "http://localhost:3000",
            "http://localhost:3001",
            "https://yourdomain.com"
        ],
        "ExposeHeaders": [
            "ETag",
            "x-amz-server-side-encryption",
            "x-amz-request-id",
            "x-amz-id-2"
        ],
        "MaxAgeSeconds": 3000
    }
]
```

6. Замените `https://yourdomain.com` на ваш реальный домен (если есть)
7. Сохраните изменения

## Через AWS CLI

```bash
aws s3api put-bucket-cors \
    --bucket kwork-project \
    --cors-configuration file://cors-config.json
```

Где `cors-config.json` содержит:

```json
{
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
            "AllowedOrigins": [
                "http://localhost:3000",
                "http://localhost:3001",
                "https://yourdomain.com"
            ],
            "ExposeHeaders": [
                "ETag",
                "x-amz-server-side-encryption",
                "x-amz-request-id",
                "x-amz-id-2"
            ],
            "MaxAgeSeconds": 3000
        }
    ]
}
```

## Через Python/boto3

Вы можете добавить эту функцию в ваш код для автоматической настройки CORS:

```python
def setup_s3_cors():
    """Setup CORS configuration for S3 bucket"""
    cors_configuration = {
        'CORSRules': [
            {
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
                'AllowedOrigins': [
                    'http://localhost:3000',
                    'http://localhost:3001',
                    # Добавьте ваш production домен
                ],
                'ExposeHeaders': [
                    'ETag',
                    'x-amz-server-side-encryption',
                    'x-amz-request-id',
                    'x-amz-id-2'
                ],
                'MaxAgeSeconds': 3000
            }
        ]
    }
    
    s3_client.put_bucket_cors(
        Bucket=settings.AWS_S3_BUCKET_NAME,
        CORSConfiguration=cors_configuration
    )
```

## Важные замечания

1. **AllowedOrigins**: Укажите все домены, с которых будет происходить загрузка
2. **AllowedMethods**: `PUT` обязателен для presigned URL загрузки
3. **AllowedHeaders**: `*` разрешает все заголовки (можно ограничить при необходимости)
4. После изменения CORS политики изменения могут применяться до нескольких минут

## Проверка

После настройки CORS, ошибка `Access-Control-Allow-Origin` должна исчезнуть, и загрузка файлов из браузера будет работать корректно.

