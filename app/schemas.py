from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from typing import Optional, Dict

class UserBase(BaseModel):
    email: EmailStr
    username: str
    preferred_language: str = "en"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    auto_translate: bool  # Add this line

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    
class UserLogin(BaseModel):
    email: str
    password: str

class TokenData(BaseModel):
    email: Optional[str] = None
    
class MessageBase(BaseModel):
    content: str
    original_language: str = "en"

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    sender_id: int
    sender: UserResponse
    created_at: datetime
    translations: Optional[Dict[str, str]] = Field(default_factory=dict)  # Changed this line

    class Config:
        from_attributes = True