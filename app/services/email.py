import smtplib
from email.message import EmailMessage
from typing import Optional

import resend

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


def _send_via_resend(to_email: str, subject: str, body: str) -> bool:
    api_key = settings.RESEND_API_KEY
    sender = settings.RESEND_FROM or settings.SMTP_FROM
    if not api_key or not sender:
        return False
    try:
        resend.api_key = api_key
        resend.Emails.send(
            {
                "from": sender,
                "to": to_email,
                "subject": subject,
                "html": body,
            }
        )
        print(f"[email:resend] sent to={to_email} subject={subject}")
        return True
    except Exception as exc:
        print(f"[email:resend:error] {exc}")
        return False


def _send_via_smtp(to_email: str, subject: str, body: str) -> bool:
    if not settings.SMTP_HOST or not settings.SMTP_FROM:
        return False

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    client = _build_smtp_client()
    if not client:
        return False

    try:
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            client.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        client.send_message(msg)
        print(f"[email:smtp] sent to={to_email} subject={subject}")
        return True
    except Exception as exc:
        print(f"[email:smtp:error] {exc}")
        return False
    finally:
        try:
            client.quit()
        except Exception:
            pass


def _send_email(to_email: str, subject: str, body: str) -> None:
    if _send_via_resend(to_email, subject, body):
        return
    if _send_via_smtp(to_email, subject, body):
        return
    print(f"[email:log_only] to={to_email} subject={subject} body={body}")


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

