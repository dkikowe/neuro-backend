import smtplib
from email.message import EmailMessage
from typing import Optional

from app.core.config import get_settings

settings = get_settings()


def _build_smtp_client():
    if not settings.SMTP_HOST:
        return None
    host = settings.SMTP_HOST
    port = settings.SMTP_PORT
    if settings.SMTP_USE_SSL:
        return smtplib.SMTP_SSL(host, port)
    client = smtplib.SMTP(host, port)
    if settings.SMTP_USE_TLS:
        client.starttls()
    return client


def _send_email(to_email: str, subject: str, body: str) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_FROM:
        # fallback to log only
        print(f"[email:log_only] to={to_email} subject={subject} body={body}")
        return

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    client = _build_smtp_client()
    if not client:
        print(f"[email:log_only] to={to_email} subject={subject} body={body}")
        return

    try:
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            client.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        client.send_message(msg)
        print(f"[email] sent to={to_email} subject={subject}")
    finally:
        try:
            client.quit()
        except Exception:
            pass


def send_verification_email(email: str, token: str) -> None:
    link = f"{settings.APP_URL}/auth/verify-email?token={token}"
    subject = "Verify your email"
    body = f"Перейдите по ссылке для подтверждения email: {link}"
    _send_email(email, subject, body)


def send_reset_email(email: str, token: str) -> None:
    link = f"{settings.APP_URL}/auth/reset-password?token={token}"
    subject = "Password reset"
    body = f"Сбросить пароль: {link}"
    _send_email(email, subject, body)

