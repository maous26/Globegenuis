from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserTier


class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    home_airports: Optional[List[str]] = None
    favorite_destinations: Optional[List[str]] = None
    travel_types: Optional[List[str]] = None
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    notification_frequency: Optional[str] = None


class UserOnboarding(BaseModel):
    step: int
    data: dict


class User(UserBase):
    id: int
    tier: UserTier
    is_active: bool
    is_verified: bool
    onboarding_step: int
    onboarding_completed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None