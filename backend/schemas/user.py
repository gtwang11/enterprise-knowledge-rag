"""用户相关 Schema"""

from typing import Optional
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern=r'^[a-zA-Z0-9_]+$')
    display_name: str = Field(..., min_length=2, max_length=50)
    phone: str = Field(..., min_length=11, max_length=11, pattern=r'^\d{11}$')
    role: str = Field(..., pattern=r'^(operator|expert)$')
    email: Optional[str] = None
    department: str = Field(..., min_length=1, max_length=50)
    remark: Optional[str] = None


class UserUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=2, max_length=50)
    phone: Optional[str] = Field(None, min_length=11, max_length=11, pattern=r'^\d{11}$')
    email: Optional[str] = None
    department: Optional[str] = Field(None, min_length=1, max_length=50)
    role: Optional[str] = Field(None, pattern=r'^(operator|expert|admin)$')
    remark: Optional[str] = None


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    phone: str
    email: Optional[str]
    department: str
    role: str
    status: str
    is_first_login: bool
    last_login_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class UserQuery(BaseModel):
    username: Optional[str] = None
    display_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
