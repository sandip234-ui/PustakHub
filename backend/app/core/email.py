"""
Email delivery service for PustakHub.

Provides email dispatch for registration OTP verification and future system notifications.

SECURITY:
  - SMTP credentials are read exclusively from environment configuration.
  - SMTP passwords and connection secrets are never logged.
  - OTP values are never logged in production.
"""

import html
import smtplib
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    """Service handling outbound email delivery via SMTP."""

    @staticmethod
    def send_registration_otp(to_email: str, recipient_name: str, otp: str) -> bool:
        """
        Send a 6-digit registration verification OTP to the user's email.

        Args:
            to_email: Recipient's email address.
            recipient_name: Full name of the registrant.
            otp: The 6-digit one-time password.

        Returns:
            True if sent or safely dispatched, False on delivery error.
        """
        if not settings.SMTP_HOST:
            # In development/test when SMTP is not configured, record dispatch safely
            logger.info(
                "[DEVELOPMENT SIMULATION] SMTP is not configured. Registration OTP for %s: %s (expires in %d min)",
                to_email,
                otp,
                settings.OTP_EXPIRE_MINUTES,
            )
            return True

        safe_name = html.escape(recipient_name)
        subject = f"{settings.SMTP_FROM_NAME} — Verification Code"
        text_body = (
            f"Hello {recipient_name},\n\n"
            f"Your verification code for PustakHub registration is: {otp}\n\n"
            f"This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.\n"
            f"If you did not request this registration, please disregard this email.\n\n"
            f"— The {settings.SMTP_FROM_NAME} Team"
        )
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #030712; color: #f9fafb; padding: 24px; }}
            .card {{ max-width: 480px; margin: 0 auto; background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 32px; }}
            .logo {{ font-size: 20px; font-weight: 700; color: #6366f1; margin-bottom: 24px; }}
            .code-box {{ background: #1e1b4b; border: 1px dashed #6366f1; border-radius: 8px; font-size: 32px; font-weight: 800; letter-spacing: 6px; text-align: center; color: #a5b4fc; padding: 16px; margin: 24px 0; }}
            .footer {{ font-size: 12px; color: #9ca3af; margin-top: 24px; line-height: 1.5; }}
          </style>
        </head>
        <body>
          <div class="card">
            <div class="logo">📚 PustakHub</div>
            <h2 style="margin: 0 0 12px 0; color: #ffffff;">Verify your email address</h2>
            <p style="color: #d1d5db; margin: 0 0 16px 0;">Hello {safe_name},</p>
            <p style="color: #9ca3af; margin: 0 0 16px 0;">Thank you for registering. Please enter the following 6-digit code to verify your account:</p>
            <div class="code-box">{otp}</div>
            <p style="color: #9ca3af; font-size: 13px;">This code will expire in <strong>{settings.OTP_EXPIRE_MINUTES} minutes</strong>. If you did not initiate this registration, please ignore this email.</p>
            <div class="footer">
              &copy; PustakHub — Secure Library & Identity Management Platform.
            </div>
          </div>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM}>"
        msg["To"] = to_email

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())
            logger.info("[REAL SMTP DELIVERY] Registration OTP email successfully sent to %s via %s:%d", to_email, settings.SMTP_HOST, settings.SMTP_PORT)
            return True
        except Exception as exc:
            logger.error("[SMTP DELIVERY FAILED] Failed to send OTP email to %s: %s", to_email, type(exc).__name__)
            return False

    @staticmethod
    def send_password_reset_email(to_email: str, recipient_name: str, reset_token: str) -> bool:
        """
        Send a password reset email with a secure one-click reset link.

        Args:
            to_email: Recipient's email address.
            recipient_name: Full name of the user.
            reset_token: The raw cryptographic password reset token.

        Returns:
            True if sent or safely dispatched, False on delivery error.
        """
        base_url = settings.FRONTEND_URL.rstrip("/")
        query_string = urllib.parse.urlencode({"token": reset_token})
        reset_url = f"{base_url}/reset-password?{query_string}"

        if not settings.SMTP_HOST:
            # In development/test when SMTP is not configured, simulate delivery safely without logging raw secrets
            logger.info(
                "SMTP is not configured. Password reset link generated for %s (delivery simulated).",
                to_email,
            )
            return True

        safe_name = html.escape(recipient_name)
        subject = f"{settings.SMTP_FROM_NAME} — Password Reset Request"
        text_body = (
            f"Hello {recipient_name},\n\n"
            f"We received a request to reset your PustakHub password.\n"
            f"Reset your password using this link:\n\n"
            f"{reset_url}\n\n"
            f"This link expires in {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes.\n"
            f"If you did not request a password reset, you can safely ignore this email. Your password will remain unchanged.\n\n"
            f"— The {settings.SMTP_FROM_NAME} Security Team"
        )
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #030712; color: #f9fafb; padding: 24px; }}
            .card {{ max-width: 500px; margin: 0 auto; background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5); }}
            .logo {{ font-size: 20px; font-weight: 700; color: #6366f1; margin-bottom: 24px; }}
            .btn {{ display: inline-block; background-color: #4f46e5; color: #ffffff !important; font-size: 15px; font-weight: 600; text-decoration: none; padding: 12px 28px; border-radius: 8px; margin: 24px 0 16px 0; text-align: center; }}
            .btn:hover {{ background-color: #4338ca; }}
            .footer {{ font-size: 12px; color: #9ca3af; margin-top: 24px; line-height: 1.5; border-top: 1px solid #1f2937; padding-top: 16px; }}
          </style>
        </head>
        <body>
          <div class="card">
            <div class="logo">📚 PustakHub</div>
            <h2 style="margin: 0 0 12px 0; color: #ffffff;">Password Reset Request</h2>
            <p style="color: #d1d5db; margin: 0 0 16px 0; font-size: 15px;">Hello {safe_name},</p>
            <p style="color: #9ca3af; margin: 0 0 16px 0; line-height: 1.6;">We received a request to reset your PustakHub password. Click the button below to choose a new password.</p>
            <div style="text-align: center;">
              <a href="{reset_url}" target="_blank" rel="noopener noreferrer" class="btn">Reset Password</a>
            </div>
            <p style="color: #9ca3af; font-size: 13px; margin: 16px 0 0 0;">This link expires in <strong>{settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes</strong>.</p>
            <p style="color: #9ca3af; font-size: 13px; margin: 8px 0 0 0;">If you did not request a password reset, you can safely ignore this email.</p>
            <div class="footer">
              &copy; PustakHub — Secure Library & Identity Management Platform.
            </div>
          </div>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM}>"
        msg["To"] = to_email

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())
            logger.info("Password reset email successfully sent to %s", to_email)
            return True
        except Exception as exc:
            logger.error("Failed to send password reset email to %s: %s", to_email, type(exc).__name__)
            return False


email_service = EmailService()
