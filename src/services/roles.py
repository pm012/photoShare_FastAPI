from typing import List
from fastapi import Depends, HTTPException, status
from src.database.models import User, UserRole
from src.services.auth import auth_service

class RoleAccess:
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(auth_service.get_current_user)):
        # Якщо роль користувача не входить у список дозволених — повертаємо 403 Forbidden
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted. Insufficient permissions."
            )
        return current_user
