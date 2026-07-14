from fastapi import APIRouter

from app.core.deps import AdminUserDep, DbDep
from app.schemas.family import FamilyCreate, FamilyResponse, FamilyUpdate
from app.services import family_service
from app.utils.response import success

router = APIRouter(prefix="/api/families", tags=["families"])


@router.post("")
def create_family(data: FamilyCreate, db: DbDep, current_user: AdminUserDep):
    family = family_service.create_family(db, current_user, data)
    return success(FamilyResponse.model_validate(family).model_dump(), "创建成功")


@router.get("")
def list_families(db: DbDep, current_user: AdminUserDep):
    families = family_service.list_families(db, current_user)
    items = [FamilyResponse.model_validate(f).model_dump() for f in families]
    return success(items)


@router.get("/{family_id}/stats")
def get_family_stats(family_id: int, db: DbDep, current_user: AdminUserDep):
    stats = family_service.get_family_stats(db, family_id, current_user)
    return success(stats.model_dump())


@router.get("/{family_id}")
def get_family(family_id: int, db: DbDep, current_user: AdminUserDep):
    family = family_service.get_family(db, family_id, current_user)
    return success(FamilyResponse.model_validate(family).model_dump())


@router.put("/{family_id}")
def update_family(
    family_id: int, data: FamilyUpdate, db: DbDep, current_user: AdminUserDep
):
    family = family_service.update_family(db, family_id, current_user, data)
    return success(FamilyResponse.model_validate(family).model_dump(), "更新成功")


@router.delete("/{family_id}")
def delete_family(family_id: int, db: DbDep, current_user: AdminUserDep):
    family_service.delete_family(db, family_id, current_user)
    return success(message="删除成功")
