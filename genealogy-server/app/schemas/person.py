from datetime import date, datetime

from pydantic import BaseModel, Field


class PersonCreate(BaseModel):
    family_id: int
    name: str = Field(min_length=1, max_length=50)
    nickname: str = Field(min_length=1, max_length=50)
    gender: int = Field(default=1, ge=0, le=2)
    generation: int = Field(ge=1)
    birth_year: int = Field(ge=1000, le=2100)
    birth_date: date | None = None
    death_date: date | None = None
    birthplace: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=200)
    biography: str | None = None
    remark: str | None = None
    is_alive: int = Field(default=1, ge=0, le=1)
    avatar_url: str | None = Field(default=None, max_length=255)


class PersonUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    nickname: str | None = Field(default=None, min_length=1, max_length=50)
    gender: int | None = Field(default=None, ge=0, le=2)
    generation: int | None = Field(default=None, ge=1)
    birth_year: int | None = Field(default=None, ge=1000, le=2100)
    birth_date: date | None = None
    death_date: date | None = None
    birthplace: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=200)
    biography: str | None = None
    remark: str | None = None
    is_alive: int | None = Field(default=None, ge=0, le=1)
    avatar_url: str | None = Field(default=None, max_length=255)


class PersonResponse(BaseModel):
    id: int
    family_id: int
    name: str
    nickname: str
    gender: int
    generation: int | None
    birth_year: int | None
    birth_date: date | None
    death_date: date | None
    birthplace: str | None
    phone: str | None = None
    address: str | None = None
    biography: str | None
    remark: str | None
    is_alive: int
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PersonListResponse(BaseModel):
    total: int
    items: list[PersonResponse]
