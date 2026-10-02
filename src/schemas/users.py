from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from src.database.models import UserRole
from typing import Optional

# Scheme for public user profile (accessible to everyone)
class UserPublicResponse(BaseModel):
    username: str
    created_at: datetime
    avatar_url: Optional[str] = None
    photos_count: int  # Requirements: Number of uploaded photos

    model_config = ConfigDict(from_attributes=True)

# Detailed user profile
class UserMeResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# Scheme for editing the user's own profile
class UserUpdateModel(BaseModel):
    username: str
    avatar_url: Optional[str] = None

# Scheme for editing the role of a non-admin user by an admin
class UserRoleUpdateModel(BaseModel):
    role: UserRole
