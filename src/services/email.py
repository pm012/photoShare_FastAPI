from datetime import datetime, timedelta, timezone
import jwt
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

from src.conf.config import settings

# Налаштування підключення до вашого SMTP-серверу (Gmail/Ukr.net тощо)
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

# Створення унікального токена підтвердження пошти на 24 години
def create_email_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode.update({"exp": expire, "scope": "email_verification"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def send_verification_email(email: EmailStr, username: str, host: str):
    token = create_email_token({"sub": email})
    verification_url = f"{host}api/auth/confirmed/{token}"

    html_content = f"""
    <p>Привіт, {username}!</p>
    <p>Дякуємо за реєстрацію в PhotoShare. Будь ласка, підтвердіть свій email, клікнувши за посиланням нижче:</p>
    <a href="{verification_url}">Підтвердити реєстрацію</a>
    <p>Посилання дійсне 24 години.</p>
    """

    message = MessageSchema(
        subject="Підтвердження реєстрації PhotoShare",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html,
        mail_from=settings.MAIL_FROM # для UKR.NET буде помилка якщо не вказати адресу яка буде співпадати з поштою аккаунта
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    
async def send_reset_password_email(email: EmailStr, username: str, host: str):
    # Генеруємо токен із scope "password_reset" на 1 годину
    to_encode = {"sub": email, "exp": datetime.now(timezone.utc) + timedelta(hours=1), "scope": "password_reset"}
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    reset_url = f"{host}api/auth/reset_password/{token}"

    html_content = f"""
    <p>Вітаємо, {username}!</p>
    <p>Ви запросили відновлення паролю в PhotoShare. Перейдіть за посиланням для встановлення нового паролю:</p>
    <a href="{reset_url}">Скинути пароль</a>
    <p>Якщо ви цього не робили, просто ігноруйте цей лист.</p>
    """
    
    # Параметр mail_from, щоб Ukr.net не видавав помилку 554
    message = MessageSchema(
        subject="Відновлення паролю PhotoShare",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html,
        mail_from=settings.MAIL_FROM  # для UKR.NET буде помилка якщо не вказати адресу яка буде співпадати з поштою аккаунта
    )
    
    await FastMail(conf).send_message(message)


