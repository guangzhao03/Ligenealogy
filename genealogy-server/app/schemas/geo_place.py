from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

PlaceType = Literal["distribution", "cemetery"]


class GeoPlaceCreate(BaseModel):
    family_id: int
    place_type: PlaceType
    name: str = Field(min_length=1, max_length=100)
    longitude: Decimal = Field(ge=-180, le=180)
    latitude: Decimal = Field(ge=-90, le=90)
    address: str | None = Field(default=None, max_length=200)
    description: str | None = None
    related_person_id: int | None = None


class GeoPlaceUpdate(BaseModel):
    place_type: PlaceType | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    address: str | None = Field(default=None, max_length=200)
    description: str | None = None
    related_person_id: int | None = None


class GeoPlaceResponse(BaseModel):
    id: int
    family_id: int
    place_type: str
    name: str
    longitude: float
    latitude: float
    address: str | None
    description: str | None
    related_person_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
