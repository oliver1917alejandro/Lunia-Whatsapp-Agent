"""
EmailService: Send emails via Gmail SMTP
"""
from email.message import EmailMessage
import aiosmtplib
from src.core.config import Config
from src.core.logger import logger


class EmailService:
    """Async service to send emails via SMTP using aiosmtplib."""

    def __init__(self):
        self.server = Config.SMTP_SERVER
        self.port = Config.SMTP_PORT
        self.user = Config.SMTP_USER
        self.password = Config.SMTP_PASSWORD

        if not all([self.server, self.port, self.user, self.password]):
            logger.error("EmailService: SMTP configuration is incomplete.")
            raise ValueError("Incomplete SMTP configuration for EmailService.")

    async def send_email(self, to: str, subject: str, body: str) -> bool:
        """
        Send a plain-text email asynchronously.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text

        Returns:
            True if sent successfully, False otherwise
        """
        message = EmailMessage()
        message["From"] = self.user
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        try:
            await aiosmtplib.send(
                message,
                hostname=self.server,
                port=self.port,
                start_tls=True,
                username=self.user,
                password=self.password,
            )
            logger.info(f"Email sent to {to}.")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False
