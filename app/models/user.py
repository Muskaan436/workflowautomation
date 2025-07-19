from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid

class User(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: Optional[str] = None
    created_at: datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: Optional[str] = None

class UserIntegration(BaseModel):
    id: int
    user_id: uuid.UUID
    provider: str
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    scopes: Optional[str] = None
    created_at: datetime