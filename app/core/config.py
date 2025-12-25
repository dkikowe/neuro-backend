from functools import lru_cache
from typing import Optional, Any
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI Service API"
    APP_ENV: str = "production"
    APP_URL: str = "https://interioeaihub.com"

    BACKEND_CORS_ORIGINS: str = "*"  # comma-separated list

    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # S3 Configuration - поддерживаем оба варианта имен (старые и новые)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET_NAME: Optional[str] = None
    AWS_S3_REGION: str = "us-east-1"
    AWS_S3_ENDPOINT_URL: Optional[str] = None

    # Redis/Celery Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # Stability AI Configuration
    AI_KEY: Optional[str] = None
    STABILITY_AI_KEY: Optional[str] = None

    # SMTP
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    RESEND_API_KEY: Optional[str] = None
    RESEND_FROM: Optional[str] = None

    # Robokassa
    ROBOKASSA_LOGIN: Optional[str] = None
    ROBOKASSA_PASSWORD_1: Optional[str] = None
    ROBOKASSA_PASSWORD_2: Optional[str] = None
    ROBOKASSA_IS_TEST: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Игнорируем лишние поля в .env
    )

    @model_validator(mode="before")
    @classmethod
    def map_env_names(cls, data: Any) -> Any:
        """Маппинг имен переменных из .env на внутренние имена"""
        if isinstance(data, dict):
            result = dict(data)
            
            # Маппинг: имя_в_env -> внутреннее_имя
            mappings = [
                ("AWS_ACCESS_KEY", "AWS_ACCESS_KEY_ID"),
                ("aws_access_key", "AWS_ACCESS_KEY_ID"),
                ("AWS_ACCESS_KEY_ID", "AWS_ACCESS_KEY_ID"),
                ("AWS_SECRET_KEY", "AWS_SECRET_ACCESS_KEY"),
                ("aws_secret_key", "AWS_SECRET_ACCESS_KEY"),
                ("AWS_SECRET_ACCESS_KEY", "AWS_SECRET_ACCESS_KEY"),
                ("AWS_BUCKET_NAME", "AWS_S3_BUCKET_NAME"),
                ("aws_bucket_name", "AWS_S3_BUCKET_NAME"),
                ("AWS_S3_BUCKET_NAME", "AWS_S3_BUCKET_NAME"),
                ("REGION", "AWS_S3_REGION"),
                ("region", "AWS_S3_REGION"),
                ("AWS_S3_REGION", "AWS_S3_REGION"),
            ]
            
            for env_name, internal_name in mappings:
                # Проверяем все варианты регистра
                for key in [env_name, env_name.upper(), env_name.lower()]:
                    if key in data and internal_name not in result:
                        result[internal_name] = data[key]
                        break
            
            return result
        
        return data

    @model_validator(mode="after")
    def validate_required_fields(self):
        """Проверка обязательных полей после маппинга"""
        if not self.AWS_ACCESS_KEY_ID:
            raise ValueError("AWS_ACCESS_KEY_ID (или aws_access_key) обязателен")
        if not self.AWS_SECRET_ACCESS_KEY:
            raise ValueError("AWS_SECRET_ACCESS_KEY (или aws_secret_key) обязателен")
        if not self.AWS_S3_BUCKET_NAME:
            raise ValueError("AWS_S3_BUCKET_NAME (или aws_bucket_name) обязателен")
        if not self.AI_KEY:
            raise ValueError("AI_KEY обязателен для генерации изображений")
        
        # Убедимся, что значения не содержат лишних пробелов или кавычек
        # Важно: не трогаем содержимое секретного ключа, только убираем внешние кавычки и пробелы
        self.AWS_ACCESS_KEY_ID = self.AWS_ACCESS_KEY_ID.strip().strip('"').strip("'")
        # Для секретного ключа важно сохранить все символы, включая +, =, / и т.д.
        secret = self.AWS_SECRET_ACCESS_KEY.strip()
        # Убираем только внешние кавычки, но сохраняем все внутренние символы
        if (secret.startswith('"') and secret.endswith('"')) or (secret.startswith("'") and secret.endswith("'")):
            self.AWS_SECRET_ACCESS_KEY = secret[1:-1]
        else:
            self.AWS_SECRET_ACCESS_KEY = secret
        self.AWS_S3_BUCKET_NAME = self.AWS_S3_BUCKET_NAME.strip().strip('"').strip("'")
        self.AWS_S3_REGION = self.AWS_S3_REGION.strip().strip('"').strip("'")
        
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


