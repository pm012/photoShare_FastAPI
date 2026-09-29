from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from src.database.models import UserRole
from typing import Optional

# Публічний профіль користувача (доступний усім)
class UserPublicResponse(BaseModel):
    username: str
    created_at: datetime
    avatar_url: Optional[str] = None
    photos_count: int  # ТЗ: Кількість завантажених фото

    model_config = ConfigDict(from_attributes=True)

# Детальний власний профіль
class UserMeResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# Схема для редагування власного профілю
class UserUpdateModel(BaseModel):
    username: str
    avatar_url: Optional[str] = None

# Схема для редагування ролі не адміна адміном
class UserRoleUpdateModel(BaseModel):
    role: UserRole
