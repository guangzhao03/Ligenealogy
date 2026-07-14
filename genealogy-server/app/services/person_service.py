from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.user import User
from app.schemas.person import PersonCreate, PersonUpdate
from app.services import family_service
from app.utils.exceptions import NotFoundException


def _get_owned_person(db: Session, person_id: int, current_user: User) -> Person:
    person = db.get(Person, person_id)
    if person is None:
        raise NotFoundException("人物不存在")
    family_service.get_family(db, person.family_id, current_user)
    return person


def create_person(db: Session, current_user: User, data: PersonCreate) -> Person:
    family_service.get_family(db, data.family_id, current_user)
    person = Person(**data.model_dump())
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


def list_persons(
    db: Session,
    current_user: User,
    family_id: int,
    keyword: str | None = None,
    generation: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Person], int]:
    family_service.get_family(db, family_id, current_user)

    query = select(Person).where(Person.family_id == family_id)
    if keyword:
        query = query.where(Person.name.contains(keyword) | Person.nickname.contains(keyword))
    if generation is not None:
        query = query.where(Person.generation == generation)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    offset = (page - 1) * page_size
    items = list(
        db.scalars(
            query.order_by(Person.id.desc()).offset(offset).limit(page_size)
        ).all()
    )
    return items, total


def get_person(db: Session, person_id: int, current_user: User) -> Person:
    return _get_owned_person(db, person_id, current_user)


def update_person(
    db: Session, person_id: int, current_user: User, data: PersonUpdate
) -> Person:
    person = _get_owned_person(db, person_id, current_user)
    payload = data.model_dump(exclude_unset=True)
    # 清空现住址时同步清空坐标
    if "address" in payload and not payload.get("address"):
        payload["address_lng"] = None
        payload["address_lat"] = None
    for key, value in payload.items():
        setattr(person, key, value)
    db.commit()
    db.refresh(person)
    return person


def delete_person(db: Session, person_id: int, current_user: User) -> None:
    from app.services import media_service

    person = _get_owned_person(db, person_id, current_user)
    disk_paths = media_service.delete_person_media(db, person.id)
    db.delete(person)
    db.commit()

    for disk_path in disk_paths:
        try:
            if disk_path.exists():
                disk_path.unlink()
        except OSError:
            pass
