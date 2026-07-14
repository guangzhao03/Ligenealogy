from datetime import datetime

from pydantic import BaseModel, Field


class FamilyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    origin_place: str | None = Field(default=None, max_length=100)


class FamilyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    origin_place: str | None = Field(default=None, max_length=100)


class FamilyResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    description: str | None
    origin_place: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
