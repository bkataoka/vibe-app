from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict

from schemas.base import BaseSchema, BaseCreateSchema, BaseUpdateSchema


class UserBase(BaseModel):
    """Base schema for User"""
    model_config = ConfigDict(from_attributes=True)
    
    email: EmailStr
    full_name: str
    is_superuser: bool = False


class UserCreate(BaseCreateSchema, UserBase):
    """Schema for creating a new user"""
    password: str


class UserUpdate(BaseUpdateSchema):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_superuser: Optional[bool] = None


class UserInDBBase(BaseSchema, UserBase):
    """Base schema for User in DB (includes all common fields)"""
    pass


class User(UserInDBBase):
    """Schema for User without sensitive data"""
    pass


class UserInDB(UserInDBBase):
    """Schema for User with sensitive data (for internal use)"""
    hashed_password: str


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for authentication token"""
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    """Schema for token payload"""
    sub: int  # user_id
    exp: int  # expiration time 