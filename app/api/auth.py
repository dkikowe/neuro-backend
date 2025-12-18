from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
import secrets

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
import bcrypt
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User
from pydantic import BaseModel, EmailStr

from app.schemas.user import UserCreate, UserResponse
from app.services.redis_client import get_redis
from app.services.security import generate_token_with_expiry, hash_token
from app.services.email import send_verification_email, send_reset_email
from app.services.generations import get_or_create_balance


class RefreshTokenRequest(BaseModel):
    refresh_token: str

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


router = APIRouter(prefix="/auth", tags=["auth"])

settings = get_settings()
redis_client = get_redis()

VERIFICATION_TTL_MINUTES = 30
RESET_TTL_MINUTES = 30
RESEND_COOLDOWN_SECONDS = 60
RESEND_DAILY_LIMIT = 20
RESEND_DAILY_LIMIT_IP = 50

REG_IP_LIMIT_DAY = 5
REG_IP_LIMIT_10MIN = 3
REG_DOMAIN_LIMIT_DAY = 20
REG_DOMAIN_LIMIT_HOUR = 5
DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "tempmail.com",
    "10minutemail.com",
    "guerrillamail.com",
    "trashmail.com",
}


def _hash_password(password: str) -> str:
    # Truncate password to 72 bytes (bcrypt limit)
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    # Truncate password to 72 bytes (bcrypt limit)
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def _rate_limit(key: str, limit: int, expire_seconds: int) -> None:
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, expire_seconds)
    if current > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много запросов",
        )


def _is_disposable_domain(email: str) -> bool:
    domain = email.split("@")[-1].lower()
    return domain in DISPOSABLE_DOMAINS


def _create_token(data: dict, expires_delta: timedelta, secret_key: str) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: int) -> str:
    return _create_token(
        {"sub": str(user_id)},
        timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        settings.JWT_SECRET_KEY,
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        {"sub": str(user_id)},
        timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        settings.JWT_REFRESH_SECRET_KEY,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_in: UserCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    ip = request.client.host if request.client else "unknown"

    # Anti-abuse: IP limits
    _rate_limit(f"reg:ip:{ip}:day", REG_IP_LIMIT_DAY, 24 * 3600)
    _rate_limit(f"reg:ip:{ip}:10m", REG_IP_LIMIT_10MIN, 600)

    # Anti-abuse: domain limits
    if _is_disposable_domain(user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Временные email-домены запрещены",
        )
    domain = user_in.email.split("@")[-1].lower()
    _rate_limit(f"reg:domain:{domain}:day", REG_DOMAIN_LIMIT_DAY, 24 * 3600)
    _rate_limit(f"reg:domain:{domain}:hour", REG_DOMAIN_LIMIT_HOUR, 3600)

    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )

    token, token_hash, expires_at = generate_token_with_expiry(VERIFICATION_TTL_MINUTES)
    now = datetime.utcnow()

    user = User(
        email=user_in.email,
        hashed_password=_hash_password(user_in.password),
        status="pending_email_verification",
        email_verification_token_hash=token_hash,
        email_verification_expires_at=expires_at,
        last_verification_sent_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Инициализируем баланс генераций (1 бесплатная)
    get_or_create_balance(db, user)

    send_verification_email(user.email, token)
    return user


@router.post("/login")
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not _verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email не подтверждён",
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
def refresh_token(
    token_data: RefreshTokenRequest,
    db: Annotated[Session, Depends(get_db)],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить refresh токен",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token_data.refresh_token,
            settings.JWT_REFRESH_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            raise credentials_exception
        
        # Преобразуем user_id в int (может прийти как строка)
        user_id = int(user_id_raw) if isinstance(user_id_raw, (int, str)) else None
        if user_id is None:
            raise credentials_exception
    except (jwt.JWTError, ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    new_access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.get("/verify-email")
def verify_email(
    token: str,
    db: Annotated[Session, Depends(get_db)],
):
    token_hash = hash_token(token)
    user = (
        db.query(User)
        .filter(
            User.email_verification_token_hash == token_hash,
            User.email_verification_expires_at != None,
        )
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный токен",
        )

    if user.email_verification_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Токен просрочен",
        )

    user.status = "active"
    user.email_verification_token_hash = None
    user.email_verification_expires_at = None
    db.add(user)
    db.commit()
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return {
        "message": "Email подтверждён",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user


class ResendVerificationRequest(BaseModel):
    email: EmailStr


@router.post("/resend-verification")
def resend_verification(
    payload: ResendVerificationRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    ip = request.client.host if request.client else "unknown"
    email = payload.email.lower()

    # cooldown per email
    if redis_client.get(f"resend:cooldown:{email}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком часто, попробуйте позже",
        )

    # daily limits
    _rate_limit(f"resend:email:{email}:day", RESEND_DAILY_LIMIT, 24 * 3600)
    _rate_limit(f"resend:ip:{ip}:day", RESEND_DAILY_LIMIT_IP, 24 * 3600)

    redis_client.setex(f"resend:cooldown:{email}", RESEND_COOLDOWN_SECONDS, "1")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"message": "OK"}  # не раскрываем

    if user.status == "active":
        return {"message": "OK"}  # уже активен

    token, token_hash, expires_at = generate_token_with_expiry(VERIFICATION_TTL_MINUTES)
    now = datetime.utcnow()
    user.email_verification_token_hash = token_hash
    user.email_verification_expires_at = expires_at
    user.last_verification_sent_at = now
    db.add(user)
    db.commit()

    send_verification_email(user.email, token)
    return {"message": "OK"}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
):
    email = payload.email.lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    token, token_hash, expires_at = generate_token_with_expiry(RESET_TTL_MINUTES)
    user.reset_token_hash = token_hash
    user.reset_token_expires_at = expires_at
    db.add(user)
    db.commit()

    send_reset_email(user.email, token)
    return {"message": "OK"}


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
):
    token_hash = hash_token(payload.token)
    user = (
        db.query(User)
        .filter(
            User.reset_token_hash == token_hash,
            User.reset_token_expires_at != None,
        )
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный токен",
        )
    if user.reset_token_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Токен просрочен",
        )

    user.hashed_password = _hash_password(payload.password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    db.add(user)
    db.commit()
    return {"message": "Пароль успешно обновлён"}


