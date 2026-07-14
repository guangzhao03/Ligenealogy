from pydantic import BaseModel, Field

from app.schemas.person import PersonResponse
from app.schemas.relation_type import RelationType


class RelationCreate(BaseModel):
    family_id: int
    from_person_id: int
    to_person_id: int
    relation_type: RelationType


class RelationItemResponse(BaseModel):
    id: int
    family_id: int
    from_person_id: int
    to_person_id: int
    relation_type: str
    from_person: PersonResponse | None = None
    to_person: PersonResponse | None = None


class PersonRelationsResponse(BaseModel):
    parents: list[PersonResponse]
    children: list[PersonResponse]
    spouses: list[PersonResponse]
    siblings: list[PersonResponse]
