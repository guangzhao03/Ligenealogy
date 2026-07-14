"""Public read-only portal data, bound to a single display family."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.family import Family
from app.models.person import Person
from app.models.user import User
from app.schemas.person import PersonListResponse, PersonResponse
from app.schemas.relation import PersonRelationsResponse
from app.schemas.tree import FamilyStatsResponse, TreeGraphResponse
from app.services import person_service, relation_service, tree_service
from app.utils.exceptions import ForbiddenException, NotFoundException

GENDER_MALE = 1
GENDER_FEMALE = 2


def get_display_family(db: Session) -> Family:
    if settings.display_family_id is not None:
        family = db.get(Family, settings.display_family_id)
        if family is None:
            raise NotFoundException("展示家族不存在，请检查 DISPLAY_FAMILY_ID")
        return family

    families = list(db.scalars(select(Family).order_by(Family.id.desc())).all())
    if not families:
        raise NotFoundException("尚未配置可展示的家族")
    if len(families) == 1:
        return families[0]

    family_ids = [family.id for family in families]
    counts = db.execute(
        select(Person.family_id, func.count())
        .where(Person.family_id.in_(family_ids))
        .group_by(Person.family_id)
    ).all()
    count_map = {family_id: count for family_id, count in counts}
    return max(families, key=lambda family: (count_map.get(family.id, 0), family.id))


def _display_owner(db: Session, family: Family) -> User:
    owner = db.get(User, family.owner_id)
    if owner is None:
        raise NotFoundException("展示家族所有者不存在")
    return owner


def _ensure_person_in_display_family(db: Session, person_id: int, family: Family) -> Person:
    person = db.get(Person, person_id)
    if person is None or person.family_id != family.id:
        raise NotFoundException("人物不存在或不属于展示家族")
    return person


def get_family_overview(db: Session) -> dict:
    family = get_display_family(db)
    persons = db.scalars(select(Person).where(Person.family_id == family.id)).all()
    generations = [p.generation for p in persons if p.generation is not None]
    min_gen = min(generations) if generations else None
    max_gen = max(generations) if generations else None
    stats = FamilyStatsResponse(
        person_count=len(persons),
        male_count=sum(1 for p in persons if p.gender == GENDER_MALE),
        female_count=sum(1 for p in persons if p.gender == GENDER_FEMALE),
        min_generation=min_gen,
        max_generation=max_gen,
        generation_span=(max_gen - min_gen + 1) if min_gen is not None and max_gen is not None else 0,
    )
    return {
        "id": family.id,
        "name": family.name,
        "description": family.description,
        "origin_place": family.origin_place,
        "stats": stats.model_dump(),
    }


def list_persons(
    db: Session,
    keyword: str | None = None,
    generation: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PersonListResponse:
    family = get_display_family(db)
    owner = _display_owner(db, family)
    items, total = person_service.list_persons(
        db,
        owner,
        family_id=family.id,
        keyword=keyword,
        generation=generation,
        page=page,
        page_size=page_size,
    )
    return PersonListResponse(
        total=total,
        items=[PersonResponse.model_validate(p) for p in items],
    )


def get_person(db: Session, person_id: int) -> PersonResponse:
    family = get_display_family(db)
    person = _ensure_person_in_display_family(db, person_id, family)
    return PersonResponse.model_validate(person)


def get_person_relations(db: Session, person_id: int) -> PersonRelationsResponse:
    family = get_display_family(db)
    _ensure_person_in_display_family(db, person_id, family)
    owner = _display_owner(db, family)
    return relation_service.get_person_relations(db, person_id, owner)


def get_full_tree(db: Session) -> TreeGraphResponse:
    family = get_display_family(db)
    owner = _display_owner(db, family)
    return tree_service.get_full_tree(db, family.id, owner)


def get_patrilineal_tree(
    db: Session,
    root_person_id: int | None = None,
    max_generations: int = 12,
) -> TreeGraphResponse:
    family = get_display_family(db)
    if root_person_id is not None:
        _ensure_person_in_display_family(db, root_person_id, family)
    owner = _display_owner(db, family)
    return tree_service.get_patrilineal_tree(
        db,
        family.id,
        owner,
        root_person_id=root_person_id,
        max_generations=max_generations,
    )


def get_lineage_tree(
    db: Session,
    person_id: int,
    up_generations: int = 5,
    down_generations: int = 5,
) -> TreeGraphResponse:
    family = get_display_family(db)
    _ensure_person_in_display_family(db, person_id, family)
    owner = _display_owner(db, family)
    return tree_service.get_lineage_tree(
        db,
        family.id,
        owner,
        person_id=person_id,
        up_generations=up_generations,
        down_generations=down_generations,
    )


def get_person_tree(
    db: Session,
    person_id: int,
    direction: str = "center",
    up_generations: int = 5,
    down_generations: int = 5,
) -> TreeGraphResponse:
    family = get_display_family(db)
    _ensure_person_in_display_family(db, person_id, family)
    owner = _display_owner(db, family)
    return tree_service.get_person_tree(
        db,
        family.id,
        owner,
        person_id=person_id,
        direction=direction,
        up_generations=up_generations,
        down_generations=down_generations,
    )


def list_geo_places(db: Session, place_type: str | None = None):
    from app.services import geo_place_service

    family = get_display_family(db)
    return geo_place_service.list_places_for_family(db, family.id, place_type=place_type)


def list_residences(db: Session):
    from app.schemas.person import ResidenceResponse

    family = get_display_family(db)
    persons = db.scalars(
        select(Person)
        .where(
            Person.family_id == family.id,
            Person.address_lng.is_not(None),
            Person.address_lat.is_not(None),
        )
        .order_by(Person.generation.asc(), Person.id.asc())
    ).all()
    return [
        ResidenceResponse(
            id=person.id,
            name=person.name,
            nickname=person.nickname,
            address=person.address,
            longitude=float(person.address_lng),
            latitude=float(person.address_lat),
            generation=person.generation,
        )
        for person in persons
    ]


def assert_public_access(optional_user: User | None) -> None:
    # future: require_viewer if settings.public_require_auth
    if settings.public_require_auth and optional_user is None:
        raise ForbiddenException("公开展示需登录后访问")
