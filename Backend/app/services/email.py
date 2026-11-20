import asyncio
import smtplib
from email.message import EmailMessage
from urllib.parse import urlencode

from app.core.config import get_settings


def send_invite_email_sync(
    *,
    recipient_email: str,
    recipient_name: str,
    raw_token: str,
) -> None:
    settings = get_settings()
    if not settings.smtp_host or not settings.smtp_from_email:
        raise RuntimeError("SMTP is not configured")

    query = urlencode({"token": raw_token})
    invite_url = f"{settings.invite_accept_url}?{query}"

    message = EmailMessage()
    message["Subject"] = "Set up your Clinic Management System account"
    message["From"] = settings.smtp_from_email
    message["To"] = recipient_email
    message.set_content(
        f"Hello {recipient_name},\n\n"
        "You have been invited to join the Clinic Management System.\n"
        f"Set your password using this link (valid for 48-72 hours):\n\n"
        f"{invite_url}\n\n"
        "If you did not expect this invitation, ignore this email."
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password or "")
        smtp.send_message(message)


async def send_invite_email(
    *,
    recipient_email: str,
    recipient_name: str,
    raw_token: str,
) -> None:
    await asyncio.to_thread(
        send_invite_email_sync,
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        raw_token=raw_token,
    )
