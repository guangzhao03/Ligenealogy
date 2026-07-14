from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.person_relation import PersonRelation
from app.models.user import User
from app.schemas.person import PersonResponse
from app.schemas.relation import PersonRelationsResponse, RelationCreate
from app.schemas.relation_type import RelationType
from app.services import family_service, person_service
from app.utils.exceptions import BadRequestException, ConflictException, NotFoundException


def _normalize_spouse_ids(from_id: int, to_id: int) -> tuple[int, int]:
    return min(from_id, to_id), max(from_id, to_id)


def _load_persons_map(db: Session, person_ids: set[int]) -> dict[int, Person]:
    if not person_ids:
        return {}
    persons = db.scalars(select(Person).where(Person.id.in_(person_ids))).all()
    return {person.id: person for person in persons}


def create_relation(db: Session, current_user: User, data: RelationCreate) -> PersonRelation:
    if data.from_person_id == data.to_person_id:
        raise BadRequestException("不能与自己建立关系")

    from_person = person_service.get_person(db, data.from_person_id, current_user)
    to_person = person_service.get_person(db, data.to_person_id, current_user)

    if from_person.family_id != to_person.family_id:
        raise BadRequestException("不能跨家族建立关系")
    if from_person.family_id != data.family_id:
        raise BadRequestException("family_id 与人物所属家族不一致")

    family_service.get_family(db, data.family_id, current_user)

    from_id = data.from_person_id
    to_id = data.to_person_id
    relation_type = data.relation_type.value

    if relation_type == RelationType.spouse.value:
        from_id, to_id = _normalize_spouse_ids(from_id, to_id)
    elif relation_type == RelationType.parent.value:
        if (
            from_person.generation is not None
            and to_person.generation is not None
            and from_person.generation >= to_person.generation
        ):
            raise BadRequestException("父母世代应小于子女世代")

    existing = db.scalar(
        select(PersonRelation).where(
            PersonRelation.family_id == data.family_id,
            PersonRelation.from_person_id == from_id,
            PersonRelation.to_person_id == to_id,
            PersonRelation.relation_type == relation_type,
        )
    )
    if existing:
        raise ConflictException("关系已存在")

    if relation_type == RelationType.spouse.value:
        reverse = db.scalar(
            select(PersonRelation).where(
                PersonRelation.family_id == data.family_id,
                PersonRelation.relation_type == RelationType.spouse.value,
                or_(
                    (PersonRelation.from_person_id == to_id)
                    & (PersonRelation.to_person_id == from_id),
                    (PersonRelation.from_person_id == from_id)
                    & (PersonRelation.to_person_id == to_id),
                ),
            )
        )
        if reverse:
            raise ConflictException("配偶关系已存在")

    relation = PersonRelation(
        family_id=data.family_id,
        from_person_id=from_id,
        to_person_id=to_id,
        relation_type=relation_type,
    )
    db.add(relation)
    db.commit()
    db.refresh(relation)
    return relation


def _get_parent_ids(db: Session, person_id: int) -> set[int]:
    rows = db.scalars(
        select(PersonRelation.from_person_id).where(
            PersonRelation.to_person_id == person_id,
            PersonRelation.relation_type == RelationType.parent.value,
        )
    ).all()
    return set(rows)


def _get_children_ids(db: Session, person_id: int) -> set[int]:
    rows = db.scalars(
        select(PersonRelation.to_person_id).where(
            PersonRelation.from_person_id == person_id,
            PersonRelation.relation_type == RelationType.parent.value,
        )
    ).all()
    return set(rows)


def _get_spouse_ids(db: Session, person_id: int) -> set[int]:
    rows = db.scalars(
        select(PersonRelation).where(
            PersonRelation.relation_type == RelationType.spouse.value,
            or_(
                PersonRelation.from_person_id == person_id,
                PersonRelation.to_person_id == person_id,
            ),
        )
    ).all()
    spouse_ids: set[int] = set()
    for row in rows:
        if row.from_person_id == person_id:
            spouse_ids.add(row.to_person_id)
        else:
            spouse_ids.add(row.from_person_id)
    return spouse_ids


def _get_sibling_ids(db: Session, person_id: int) -> set[int]:
    parent_ids = _get_parent_ids(db, person_id)
    sibling_ids: set[int] = set()
    for parent_id in parent_ids:
        sibling_ids.update(_get_children_ids(db, parent_id))
    sibling_ids.discard(person_id)
    return sibling_ids


def get_person_relations(
    db: Session, person_id: int, current_user: User
) -> PersonRelationsResponse:
    person_service.get_person(db, person_id, current_user)

    parent_ids = _get_parent_ids(db, person_id)
    child_ids = _get_children_ids(db, person_id)
    spouse_ids = _get_spouse_ids(db, person_id)
    sibling_ids = _get_sibling_ids(db, person_id)

    person_map = _load_persons_map(
        db, parent_ids | child_ids | spouse_ids | sibling_ids
    )

    def to_responses(ids: set[int]) -> list[PersonResponse]:
        return [
            PersonResponse.model_validate(person_map[pid])
            for pid in sorted(ids)
            if pid in person_map
        ]

    return PersonRelationsResponse(
        parents=to_responses(parent_ids),
        children=to_responses(child_ids),
        spouses=to_responses(spouse_ids),
        siblings=to_responses(sibling_ids),
    )


def delete_relation(db: Session, relation_id: int, current_user: User) -> None:
    relation = db.get(PersonRelation, relation_id)
    if relation is None:
        raise NotFoundException("关系不存在")
    family_service.get_family(db, relation.family_id, current_user)
    db.delete(relation)
    db.commit()
