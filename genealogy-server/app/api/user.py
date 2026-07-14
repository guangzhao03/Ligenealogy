from fastapi import APIRouter

from app.core.deps import AdminUserDep, DbDep
from app.schemas.user import UserResponse, UserRoleUpdate
from app.services import user_service
from app.utils.response import success

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
def list_users(db: DbDep, current_user: AdminUserDep):
    users = user_service.list_users(db)
    items = [UserResponse.model_validate(u).model_dump() for u in users]
    return success(items)


@router.put("/{user_id}/role")
def update_user_role(
    user_id: int,
    data: UserRoleUpdate,
    db: DbDep,
    current_user: AdminUserDep,
):
    user = user_service.update_user_role(db, user_id, data.role, current_user)
    return success(UserResponse.model_validate(user).model_dump(), "角色已更新")
