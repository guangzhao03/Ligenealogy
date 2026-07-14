from fastapi import APIRouter, Query

from app.core.deps import AdminUserDep, DbDep
from app.schemas.person import (
    PersonCreate,
    PersonListResponse,
    PersonResponse,
    PersonUpdate,
)
from app.services import person_service
from app.utils.response import success

router = APIRouter(prefix="/api/persons", tags=["persons"])


@router.post("")
def create_person(data: PersonCreate, db: DbDep, current_user: AdminUserDep):
    person = person_service.create_person(db, current_user, data)
    return success(PersonResponse.model_validate(person).model_dump(), "创建成功")


@router.get("")
def list_persons(
    db: DbDep,
    current_user: AdminUserDep,
    family_id: int = Query(...),
    keyword: str | None = Query(default=None),
    generation: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    items, total = person_service.list_persons(
        db,
        current_user,
        family_id=family_id,
        keyword=keyword,
        generation=generation,
        page=page,
        page_size=page_size,
    )
    payload = PersonListResponse(
        total=total,
        items=[PersonResponse.model_validate(p) for p in items],
    )
    return success(payload.model_dump())


@router.get("/{person_id}/media")
def list_person_media(person_id: int, db: DbDep, current_user: AdminUserDep):
    from app.services import media_service

    items = media_service.list_person_media(db, person_id, current_user)
    return success([item.model_dump() for item in items])


@router.get("/{person_id}/relations")
def get_person_relations(person_id: int, db: DbDep, current_user: AdminUserDep):
    from app.services import relation_service

    relations = relation_service.get_person_relations(db, person_id, current_user)
    return success(relations.model_dump())


@router.get("/{person_id}")
def get_person(person_id: int, db: DbDep, current_user: AdminUserDep):
    person = person_service.get_person(db, person_id, current_user)
    return success(PersonResponse.model_validate(person).model_dump())


@router.put("/{person_id}")
def update_person(
    person_id: int, data: PersonUpdate, db: DbDep, current_user: AdminUserDep
):
    person = person_service.update_person(db, person_id, current_user, data)
    return success(PersonResponse.model_validate(person).model_dump(), "更新成功")


@router.delete("/{person_id}")
def delete_person(person_id: int, db: DbDep, current_user: AdminUserDep):
    person_service.delete_person(db, person_id, current_user)
    return success(message="删除成功")
