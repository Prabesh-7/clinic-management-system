import asyncio
import smtplib
from email.message import EmailMessage
from typing import Protocol
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings


class EmailDeliveryError(RuntimeError):
    pass


class EmailProvider(Protocol):
    async def send(
        self,
        *,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
    ) -> None: ...


class ConsoleEmailProvider:
    async def send(
        self,
        *,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
    ) -> None:
        print(
            f"[EMAIL] to={recipient_email} recipient={recipient_name}\n"
            f"subject={subject}\n{text_body}"
        )


class SMTPEmailProvider:
    async def send(
        self,
        *,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
    ) -> None:
        settings = get_settings()
        from_email = settings.email_from_email or settings.smtp_from_email
        if not settings.smtp_host or not from_email:
            raise EmailDeliveryError("SMTP_HOST and a sender email are required")

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = f"{settings.email_from_name} <{from_email}>"
        message["To"] = recipient_email
        message.set_content(text_body)
        if html_body:
            message.add_alternative(html_body, subtype="html")

        def deliver() -> None:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
                if settings.smtp_use_tls:
                    smtp.starttls()
                if settings.smtp_username:
                    smtp.login(settings.smtp_username, settings.smtp_password or "")
                smtp.send_message(message)

        await asyncio.to_thread(deliver)


class ResendEmailProvider:
    async def send(
        self,
        *,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
    ) -> None:
        settings = get_settings()
        from_email = settings.email_from_email or settings.smtp_from_email
        if not settings.resend_api_key or not from_email:
            raise EmailDeliveryError(
                "RESEND_API_KEY and a sender email are required"
            )

        payload = {
            "from": f"{settings.email_from_name} <{from_email}>",
            "to": [recipient_email],
            "subject": subject,
            "text": text_body,
        }
        if html_body:
            payload["html"] = html_body

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if response.is_error:
            raise EmailDeliveryError(
                f"Email provider rejected the request: HTTP {response.status_code}"
            )


def get_email_provider() -> EmailProvider:
    settings = get_settings()
    if settings.email_provider == "console":
        return ConsoleEmailProvider()
    if settings.email_provider == "resend":
        return ResendEmailProvider()
    return SMTPEmailProvider()


async def send_invite_email(
    *,
    recipient_email: str,
    recipient_name: str,
    raw_token: str,
) -> None:
    settings = get_settings()
    query = urlencode({"token": raw_token})
    invite_url = f"{settings.invite_accept_url}?{query}"
    subject = "Set up your Clinic Management System account"
    text_body = (
        f"Hello {recipient_name},\n\n"
        "You have been invited to join the Clinic Management System.\n"
        f"Set your password using this link (valid for {settings.invite_token_hours} hours):\n\n"
        f"{invite_url}\n\n"
        "If you did not expect this invitation, ignore this email."
    )
    html_body = (
        f"<p>Hello {recipient_name},</p>"
        "<p>You have been invited to join the Clinic Management System.</p>"
        f'<p><a href="{invite_url}">Set your account password</a></p>'
        f"<p>This link is valid for {settings.invite_token_hours} hours.</p>"
    )
    await get_email_provider().send(
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )
