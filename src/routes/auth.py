import jwt

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi import Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from src.conf.config import settings
from sqlalchemy.orm import Session
from src.database.models import User

from src.database.db import get_db
from src.schemas.auth import UserModel, UserDb, TokenModel
from src.repository import auth as repository_auth
from src.services.auth import auth_service
from src.services.blacklist import blacklist_service
from src.services.limiter import  limiter
from src.services.email import send_verification_email, send_reset_password_email

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserDb, status_code=status.HTTP_201_CREATED)
@limiter.limit("2/minute")
async def signup(body: UserModel, request: Request, db: Session = Depends(get_db)):
    exist_user = repository_auth.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=409, detail="Account already exists")
    
    new_user = repository_auth.create_user(body, db)
    
    # Надсилаємо лист ТІЛЬКИ якщо верифікація увімкнена в налаштуваннях
    if settings.MAIL_CONFIRMATION_REQUIRED:
        try:
            await send_verification_email(new_user.email, new_user.username, str(request.base_url))
        except Exception as e:
            # Якщо пошта впала, ми не ламаємо реєстрацію, а просто логуємо помилку
            print(f"Email sending failed: {e}")
            
    return new_user


@router.post("/login", response_model=TokenModel)
@limiter.limit("5/minute")
def login(request: Request, body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Шукаємо користувача за email (у Swagger форму логіну поле називається username, але ми туди очікуємо email)
    user = repository_auth.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid email or password"
        )
    
    # Перевіряємо, чи не забанений користувач за ТЗ
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is banned/inactive"
        )
        
    # Перевіряємо відповідність хешу пароля
    if not auth_service.verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid email or password"
        )      

    
    # Генеруємо JWT токен доступу
    access_token = auth_service.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(token: str = Depends(oauth2_scheme), current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)):
    
    # Визначаємо час життя токена (беремо дефолтне значення з конфігурації за ТЗ)
    # Для більшої точності можна розпарсити exp з токена, але за умовою TTL = час до експірації
    expire_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    # Додаємо токен у чорний список
    blacklist_service.add_to_blacklist(token, expire_seconds)
    
    return {"message": "You have successfully logged out."}

from src.schemas.auth import RequestEmail, ResetPasswordModel
from src.services.email import send_reset_password_email

@router.post("/request_password_reset")
async def request_password_reset(body: RequestEmail, request: Request, db: Session = Depends(get_db)):
    user = repository_auth.get_user_by_email(body.email, db)
    if user:
        await send_reset_password_email(user.email, user.username, str(request.base_url))
    # Заради безпеки (захист від сканування імейлів) завжди повертаємо успіх
    return {"message": "If the email exists, a reset link has been sent."}


@router.post("/reset_password/{token}")
def reset_password(token: str, body: ResetPasswordModel, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("scope") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token scope")
        email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = repository_auth.get_user_by_email(email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Хешуємо та перезаписуємо новий пароль нативним bcrypt
    user.hashed_password = auth_service.get_password_hash(body.password)
    db.commit()
    return {"message": "Password has been successfully updated. You can now log in."}

@router.get("/confirmed/{token}")
def confirm_email(token: str, db: Session = Depends(get_db)):
    try:
        # Розшифровуємо токен та перевіряємо його призначення
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("scope") != "email_verification":
            raise HTTPException(status_code=400, detail="Invalid token scope")
        email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    # Шукаємо користувача в базі за email
    user = repository_auth.get_user_by_email(email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_confirmed:
        return {"message": "Your email is already confirmed."}
    
    # Активуємо статус верифікації
    user.is_confirmed = True
    db.commit()
    return {"message": "Email successfully confirmed! You can now log in."}

