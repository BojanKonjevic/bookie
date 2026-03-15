from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: UUID
    email: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class TagBase(BaseModel):
    name: str


class TagRead(TagBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class BookmarkBase(BaseModel):
    title: str = Field(min_length=1)
    url: HttpUrl
    favorite: bool = False
    description: str | None = None


class BookmarkCreate(BookmarkBase):
    tags: list[str] = Field(default_factory=list)


class BookmarkRead(BookmarkBase):
    id: UUID
    created_at: datetime
    tags: list[TagRead]
    model_config = ConfigDict(from_attributes=True)


class BookmarkUpdate(BaseModel):
    title: str | None = None
    url: HttpUrl | None = None
    favorite: bool | None = None
    description: str | None = None
    tags: list[str] | None = None
