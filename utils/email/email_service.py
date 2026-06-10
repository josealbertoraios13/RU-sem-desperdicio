import os
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from utils.logger import logger


class EmailService:
    """
    Service for sending emails via SMTP.
    Configure via environment variables:
    - SMTP_HOST: SMTP server host (e.g., smtp.gmail.com)
    - SMTP_PORT: SMTP server port (default: 587)
    - SMTP_USER: SMTP username
    - SMTP_PASSWORD: SMTP password
    - SMTP_FROM_EMAIL: From email address
    - SMART_RU_URL: Base URL for password reset links
    """

    _smtp_host: str | None = None
    _smtp_port: int = 587
    _smtp_user: str | None = None
    _smtp_password: str | None = None
    _from_email: str | None = None
    _initialized: bool = False

    @classmethod
    def initialize(cls):
        """Initialize email service from environment variables."""
        cls._smtp_host = os.getenv("SMTP_HOST")
        cls._smtp_port = int(os.getenv("SMTP_PORT", "587"))
        cls._smtp_user = os.getenv("SMTP_USER")
        cls._smtp_password = os.getenv("SMTP_PASSWORD")
        cls._from_email = os.getenv("SMTP_FROM_EMAIL", cls._smtp_user)
        cls._initialized = True

        if not cls._smtp_host:
            logger.warning("SMTP_HOST not configured. Email sending will be simulated.")

    @classmethod
    def send_password_reset_email(cls, to_email: str, reset_token: str, user_name: str) -> bool:
        """
        Send password reset email with token.

        Args:
            to_email: Recipient email address
            reset_token: Token for password reset
            user_name: Name of the user

        Returns:
            True if email sent successfully, False otherwise
        """
        if not cls._initialized:
            cls.initialize()

        smart_ru_url = os.getenv("SMART_RU_URL", "http://localhost:5173")
        reset_link = f"{smart_ru_url}/reset-password?token={reset_token}"

        subject = "SmartRU - Recuperação de Senha"

        # Create HTML body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">SmartRU - Recuperação de Senha</h2>
                <p>Olá, {user_name}!</p>
                <p>Você solicitou a recuperação de senha. Para redefinir sua senha, clique no link abaixo:</p>
                <p style="margin: 30px 0;">
                    <a href="{reset_link}"
                       style="background-color: #3498db; color: white; padding: 12px 30px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Redefinir Senha
                    </a>
                </p>
                <p>Ou copie e cole o link abaixo no seu navegador:</p>
                <p style="word-break: break-all; color: #3498db;">{reset_link}</p>
                <p><strong>Atenção:</strong> Este link expira em 1 hora.</p>
                <p>Se você não solicitou esta recuperação, por favor ignore este email.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin-top: 30px;">
                <p style="color: #7f8c8d; font-size: 12px;">
                    Este é um email automático, por favor não responda.
                </p>
            </div>
        </body>
        </html>
        """

        # Create text body
        text_body = f"""
        SmartRU - Recuperação de Senha

        Olá, {user_name}!

        Você solicitou a recuperação de senha. Para redefinir sua senha, acesse o link:
        {reset_link}

        Atenção: Este link expira em 1 hora.

        Se você não solicitou esta recuperação, por favor ignore este email.
        """

        try:
            if not cls._smtp_host:
                # Simulate email sending for development
                # SECURITY: Never log tokens - only log that email was sent
                logger.info(f"[EMAIL SIMULATED] Password reset email sent to {to_email}")
                return True

            # Type narrowing: at this point all SMTP config is guaranteed
            assert cls._smtp_user is not None, "SMTP_USER not configured"
            assert cls._smtp_password is not None, "SMTP_PASSWORD not configured"
            assert cls._from_email is not None, "SMTP_FROM_EMAIL not configured"

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = cls._from_email
            msg['To'] = to_email

            part1 = MIMEText(text_body, 'plain', 'utf-8')
            part2 = MIMEText(html_body, 'html', 'utf-8')

            msg.attach(part1)
            msg.attach(part2)

            server = smtplib.SMTP(cls._smtp_host, cls._smtp_port)
            server.starttls()
            server.login(cls._smtp_user, cls._smtp_password)
            server.sendmail(cls._from_email, to_email, msg.as_string())
            server.quit()

            logger.info(f"Password reset email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")
            return False

    @classmethod
    def send_test_email(cls, to_email: str) -> bool:
        """Send a test email to verify SMTP configuration."""
        if not cls._initialized:
            cls.initialize()

        subject = "SmartRU - Teste de Configuração de Email"
        body = "Configuração de email bem-sucedida! O sistema SmartRU está pronto para enviar emails."

        try:
            if not cls._smtp_host:
                logger.info(f"[EMAIL TEST SIMULATED] To: {to_email}")
                return True

            # Type narrowing: at this point all SMTP config is guaranteed
            assert cls._smtp_user is not None, "SMTP_USER not configured"
            assert cls._smtp_password is not None, "SMTP_PASSWORD not configured"
            assert cls._from_email is not None, "SMTP_FROM_EMAIL not configured"

            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = cls._from_email
            msg['To'] = to_email
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            server = smtplib.SMTP(cls._smtp_host, cls._smtp_port)
            server.starttls()
            server.login(cls._smtp_user, cls._smtp_password)
            server.sendmail(cls._from_email, to_email, msg.as_string())
            server.quit()

            logger.info(f"Test email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Error sending test email: {e}")
            return False
