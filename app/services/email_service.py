import smtplib
import asyncio
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import get_settings

logger = logging.getLogger(__name__)

async def send_invitation_email(recipient: str, org_name: str, inviter_name: str, role: str, token: str) -> None:
    subject = f"Invitation to join {org_name} on Flowdesk"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 24px;">
        <div style="max-width: 500px; margin: 0 auto; background-color: #1e293b; padding: 32px; border-radius: 12px; border: 1px solid #334155;">
            <h2 style="color: #818cf8; margin-top: 0;">Flowdesk Organization Invitation</h2>
            <p style="font-size: 15px; line-height: 1.6; color: #cbd5e1;">
                Hello,<br/><br/>
                <strong>{inviter_name}</strong> has invited you to join <strong>{org_name}</strong> as a <strong>{role.upper()}</strong>.
            </p>
            <p style="font-size: 15px; line-height: 1.6; color: #cbd5e1;">
                To accept this invitation and join the organization, please click the button below to sign up/login and get started:
            </p>
            <div style="text-align: center; margin: 24px 0;">
                <a href="http://localhost:3000/?token={token}&email={recipient}" style="background-color: #6366f1; color: #ffffff; padding: 12px 28px; border-radius: 8px; font-weight: 600; text-decoration: none; display: inline-block;">
                    Join Organization
                </a>
            </div>
            <p style="font-size: 13px; color: #94a3b8; margin-top: 16px;">
                Alternatively, you can manually use the following One-Time Invite Token: <strong>{token}</strong>
            </p>
            <p style="font-size: 13px; color: #94a3b8; margin-bottom: 0;">
                This invitation token will expire in 7 days.
            </p>
        </div>
    </body>
    </html>
    """
    
    await send_email(recipient=recipient, subject=subject, html_content=html_content)

async def send_email(recipient: str, subject: str, html_content: str) -> None:
    settings = get_settings()
    try:
        await asyncio.to_thread(
            _send_email_sync,
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            user=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            sender=settings.SMTP_FROM,
            recipient=recipient,
            subject=subject,
            html_content=html_content
        )
    except Exception as e:
        logger.error(f"Failed to send email to {recipient} via SMTP: {e}")
        raise e

def _send_email_sync(host: str, port: int, user: str | None, password: str | None, sender: str, recipient: str, subject: str, html_content: str) -> None:
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject
    
    msg.attach(MIMEText(html_content, 'html'))
    
    with smtplib.SMTP(host, port) as server:
        if user and password:
            server.starttls()
            server.login(user, password)
        server.send_message(msg)
