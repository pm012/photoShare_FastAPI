from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from src.conf.config import settings
from sqlalchemy.orm import Session
from src.database.models import User

from src.database.db import get_db
from src.schemas.auth import UserModel, UserDb, TokenModel
from src.repository import auth as repository_auth
from src.services.auth import auth_service
from src.services.blacklist import blacklist_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserDb, status_code=status.HTTP_201_CREATED)
def signup(body: UserModel, db: Session = Depends(get_db)):
    # Перевіряємо, чи користувач з таким email вже існує
    exist_user = repository_auth.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Account with this email already exists"
        )
    
    # Створюємо користувача (всередині закладена логіка: перший — ADMIN)
    new_user = repository_auth.create_user(body, db)
    return new_user


@router.post("/login", response_model=TokenModel)
def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
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
