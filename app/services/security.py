import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Tuple


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_token_with_expiry(minutes: int) -> Tuple[str, str, datetime]:
    token = generate_token()
    token_hash = hash_token(token)
    expires_at = datetime.utcnow() + timedelta(minutes=minutes)
    return token, token_hash, expires_at


