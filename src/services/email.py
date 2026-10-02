from datetime import datetime, timedelta, timezone
import jwt
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

from src.conf.config import settings

# Configuration for connecting to your SMTP server (Gmail/Ukr.net etc.)
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# Creating a unique token for email verification for 24 hours
def create_email_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode.update({"exp": expire, "scope": "email_verification"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def send_verification_email(email: EmailStr, username: str, host: str):
    token = create_email_token({"sub": email})
    verification_url = f"{host}api/auth/confirmed/{token}"

    html_content = f"""
    <p>Hello, {username}!</p>
    <p>Thank you for registering with PhotoShare. Please confirm your email by clicking the link below:</p>
    <a href="{verification_url}">Confirm Registration</a>
    <p>This link is valid for 24 hours.</p>
    """

    message = MessageSchema(
        subject="Confirmation of PhotoShare Registration",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html,
        mail_from=settings.MAIL_FROM #  for UKR.NET it will be an error if not specify the address that will match the account email
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    
async def send_reset_password_email(email: EmailStr, username: str, host: str):
    # Generate token for password reset
    to_encode = {"sub": email, "exp": datetime.now(timezone.utc) + timedelta(hours=1), "scope": "password_reset"}
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/?reset_token={token}"

    html_content = f"""
    <p>Greeting, {username}!</p>
    <p>You have requested a password reset for your PhotoShare account. Please click the link below to set a new password:</p>
    <a href="{reset_url}">Reset Password</a>
    <p>If you did not request this, please ignore this email.</p>
    """
    
    # Parameter mail_from, to ensure Ukr.net is not returning  554 error
    message = MessageSchema(
        subject="Password Reset for PhotoShare",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html,
        mail_from=settings.MAIL_FROM  #  for UKR.NET it will be an error if not specify the address that will match the account email
    )
    
    await FastMail(conf).send_message(message)


