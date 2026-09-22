import os
import smtplib

from email.message import EmailMessage
from dotenv import load_dotenv


load_dotenv()


class EmailSenderService:
    def __init__(self):
        self.emails_enabled = os.getenv("EMAILS_ENABLED", "false").lower() == "true"
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.smtp_from = os.getenv("SMTP_FROM")

    def _ensure_email_config_is_valid(self):
        if not self.smtp_host:
            raise ValueError("SMTP_HOST no está configurado")

        if not self.smtp_port:
            raise ValueError("SMTP_PORT no está configurado")

        if not self.smtp_user:
            raise ValueError("SMTP_USER no está configurado")

        if not self.smtp_password:
            raise ValueError("SMTP_PASSWORD no está configurado")

        if not self.smtp_from:
            raise ValueError("SMTP_FROM no está configurado")

    def send_email(
        self,
        to_email: str,
        subject: str,
        message: str
    ):
        if not self.emails_enabled:
            return

        self._ensure_email_config_is_valid()

        email = EmailMessage()
        email["From"] = self.smtp_from
        email["To"] = to_email
        email["Subject"] = subject
        email.set_content(message)

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as smtp:
                smtp.starttls()
                smtp.login(self.smtp_user, self.smtp_password)
                smtp.send_message(email)

        except Exception as error:
            raise RuntimeError(f"No se pudo enviar el correo: {error}")