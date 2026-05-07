from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRoleEnum(str, Enum):
    """Роли пользователей"""
    USER = "user"
    ADMIN = "admin"


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_id: int
    username: str
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        if len(v) > 128:
            raise ValueError('Password is too long (max 128 characters)')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username is too long (max 50 characters)')
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# === СХЕМЫ ДЛЯ ADMIN-ПАНЕЛИ ===

class UpdateUserRoleRequest(BaseModel):
    """Запрос на изменение роли пользователя"""
    role: UserRoleEnum
    
    class Config:
        use_enum_values = True


class UpdateUserStatusRequest(BaseModel):
    """Запрос на блокировку/разблокировку пользователя"""
    is_active: bool


class UpdateUserProfileRequest(BaseModel):
    """Запрос на обновление профиля пользователя"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if len(v) < 3:
                raise ValueError('Username must be at least 3 characters long')
            if len(v) > 50:
                raise ValueError('Username is too long (max 50 characters)')
        return v


class UserDetailedResponse(UserResponse):
    """Расширенная информация о пользователе (для админов)"""
    email: Optional[str]
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UsersStatsResponse(BaseModel):
    """Статистика по пользователям системы"""
    total_users: int
    active_users: int
    blocked_users: int
    admin_count: int
    user_count: int


class UserListResponse(BaseModel):
    """Постраничный ответ со списком пользователей"""
    items: List[UserDetailedResponse]
    total: int
    page: int
    page_size: int


class ImageItemResponse(BaseModel):
    id: int
    original_url: str
    processed_url: Optional[str] = None
    result: Optional[str] = None
    confidence: float
    filename: str
    file_size: int
    status: str
    created_at: datetime
    processed_at: Optional[datetime] = None


class ImageListResponse(BaseModel):
    """Постраничный ответ со списком изображений пользователя"""
    items: List[ImageItemResponse]
    total: int
    page: int
    page_size: int
