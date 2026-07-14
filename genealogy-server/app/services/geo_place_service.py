from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.geo_place import GeoPlace
from app.models.person import Person
from app.models.user import User
from app.schemas.geo_place import GeoPlaceCreate, GeoPlaceResponse, GeoPlaceUpdate
from app.services import family_service
from app.utils.exceptions import BadRequestException, NotFoundException

VALID_TYPES = {"distribution", "cemetery"}


def _to_response(place: GeoPlace) -> GeoPlaceResponse:
    return GeoPlaceResponse(
        id=place.id,
        family_id=place.family_id,
        place_type=place.place_type,
        name=place.name,
        longitude=float(place.longitude),
        latitude=float(place.latitude),
        address=place.address,
        description=place.description,
        related_person_id=place.related_person_id,
        created_at=place.created_at,
        updated_at=place.updated_at,
    )


def _validate_related_person(
    db: Session, family_id: int, person_id: int | None
) -> None:
    if person_id is None:
        return
    person = db.get(Person, person_id)
    if person is None or person.family_id != family_id:
        raise BadRequestException("关联人物不存在或不属于当前家族")


def _get_owned_place(db: Session, place_id: int, current_user: User) -> GeoPlace:
    place = db.get(GeoPlace, place_id)
    if place is None:
        raise NotFoundException("地理标记不存在")
    family_service.get_family(db, place.family_id, current_user)
    return place


def list_places(
    db: Session,
    current_user: User,
    family_id: int,
    place_type: str | None = None,
) -> list[GeoPlaceResponse]:
    family_service.get_family(db, family_id, current_user)
    query = select(GeoPlace).where(GeoPlace.family_id == family_id)
    if place_type:
        if place_type not in VALID_TYPES:
            raise BadRequestException("无效的地点类型")
        query = query.where(GeoPlace.place_type == place_type)
    items = list(db.scalars(query.order_by(GeoPlace.id.desc())).all())
    return [_to_response(item) for item in items]


def create_place(db: Session, current_user: User, data: GeoPlaceCreate) -> GeoPlaceResponse:
    family_service.get_family(db, data.family_id, current_user)
    _validate_related_person(db, data.family_id, data.related_person_id)
    place = GeoPlace(**data.model_dump())
    db.add(place)
    db.commit()
    db.refresh(place)
    return _to_response(place)


def update_place(
    db: Session, place_id: int, current_user: User, data: GeoPlaceUpdate
) -> GeoPlaceResponse:
    place = _get_owned_place(db, place_id, current_user)
    payload = data.model_dump(exclude_unset=True)
    if "related_person_id" in payload:
        _validate_related_person(db, place.family_id, payload["related_person_id"])
    for key, value in payload.items():
        setattr(place, key, value)
    db.commit()
    db.refresh(place)
    return _to_response(place)


def delete_place(db: Session, place_id: int, current_user: User) -> None:
    place = _get_owned_place(db, place_id, current_user)
    db.delete(place)
    db.commit()


def list_places_for_family(
    db: Session,
    family_id: int,
    place_type: str | None = None,
) -> list[GeoPlaceResponse]:
    query = select(GeoPlace).where(GeoPlace.family_id == family_id)
    if place_type:
        if place_type not in VALID_TYPES:
            raise BadRequestException("无效的地点类型")
        query = query.where(GeoPlace.place_type == place_type)
    items = list(db.scalars(query.order_by(GeoPlace.id.asc())).all())
    return [_to_response(item) for item in items]
