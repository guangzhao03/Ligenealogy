from fastapi import APIRouter, Query

from app.core.deps import AdminUserDep, DbDep, EditorUserDep
from app.schemas.geo_place import GeoPlaceCreate, GeoPlaceUpdate
from app.services import geo_place_service
from app.utils.response import success

router = APIRouter(prefix="/api/geo-places", tags=["geo-places"])


@router.get("")
def list_geo_places(
    db: DbDep,
    current_user: AdminUserDep,
    family_id: int = Query(...),
    place_type: str | None = Query(default=None),
):
    items = geo_place_service.list_places(
        db, current_user, family_id=family_id, place_type=place_type
    )
    return success([item.model_dump() for item in items])


@router.post("")
def create_geo_place(data: GeoPlaceCreate, db: DbDep, current_user: EditorUserDep):
    place = geo_place_service.create_place(db, current_user, data)
    return success(place.model_dump(), "创建成功")


@router.put("/{place_id}")
def update_geo_place(
    place_id: int, data: GeoPlaceUpdate, db: DbDep, current_user: EditorUserDep
):
    place = geo_place_service.update_place(db, place_id, current_user, data)
    return success(place.model_dump(), "更新成功")


@router.delete("/{place_id}")
def delete_geo_place(place_id: int, db: DbDep, current_user: EditorUserDep):
    geo_place_service.delete_place(db, place_id, current_user)
    return success(message="删除成功")
