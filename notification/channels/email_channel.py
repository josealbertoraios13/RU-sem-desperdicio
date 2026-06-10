"""
Email notification channel wrapping the existing EmailService.

Handles sending notification emails with proper MIME formatting
and graceful fallback to simulation mode when SMTP is not configured.
"""
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from smartru.notification.channels.base import NotificationChannel
from smartru.utils import logger
from smartru.utils.email.email_service import EmailService


class EmailNotificationChannel(NotificationChannel):
    """
    Email notification channel.

    Reuses the SMTP configuration from EmailService (SMTP_HOST, etc.)
    and provides a dict-based return format consistent with the
    notification system.
    """

    def __init__(self):
        if not EmailService._initialized:
            EmailService.initialize()

    def send(
        self,
        user_cpf: str,
        title: str,
        message: str,
        user_email: str | None = None,
        user_name: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Send a notification email.

        Args:
            user_cpf: User identifier (for logging)
            title: Email subject line
            message: HTML body content
            user_email: Recipient email address
            user_name: User's display name (for personalization)

        Returns:
            dict with keys: success, error_message
        """
        if not user_email:
            return {
                "success": False,
                "error_message": "No email address provided",
            }

        if not EmailService._smtp_host:
            logger.info(
                f"[NOTIFICATION EMAIL SIMULATED] To: {user_email} | "
                f"Subject: {title}"
            )
            return {"success": True, "error_message": None}

        # Type narrowing
        assert EmailService._smtp_user is not None
        assert EmailService._smtp_password is not None
        assert EmailService._from_email is not None

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = title
            msg["From"] = EmailService._from_email
            msg["To"] = user_email

            # Plain text fallback (strip HTML tags)
            text_body = re.sub(r"<[^>]+>", "", message)
            text_body = text_body.replace("\n\n", "\n").strip()

            part1 = MIMEText(text_body, "plain", "utf-8")
            part2 = MIMEText(message, "html", "utf-8")
            msg.attach(part1)
            msg.attach(part2)

            server = smtplib.SMTP(
                EmailService._smtp_host, EmailService._smtp_port
            )
            server.starttls()
            server.login(EmailService._smtp_user, EmailService._smtp_password)
            server.sendmail(
                EmailService._from_email, user_email, msg.as_string()
            )
            server.quit()

            logger.info(
                f"Notification email sent to {user_email} for user {user_cpf}"
            )
            return {"success": True, "error_message": None}

        except Exception as e:
            logger.error(
                f"Failed to send notification email to user {user_cpf}: {e}"
            )
            return {"success": False, "error_message": str(e)}
