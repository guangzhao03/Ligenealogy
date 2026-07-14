from fastapi import APIRouter

from app.core.deps import AdminUserDep, DbDep
from app.schemas.relation import RelationCreate
from app.services import relation_service
from app.utils.response import success

router = APIRouter(prefix="/api/relations", tags=["relations"])


@router.post("")
def create_relation(data: RelationCreate, db: DbDep, current_user: AdminUserDep):
    relation = relation_service.create_relation(db, current_user, data)
    return success(
        {
            "id": relation.id,
            "family_id": relation.family_id,
            "from_person_id": relation.from_person_id,
            "to_person_id": relation.to_person_id,
            "relation_type": relation.relation_type,
        },
        "创建成功",
    )


@router.delete("/{relation_id}")
def delete_relation(relation_id: int, db: DbDep, current_user: AdminUserDep):
    relation_service.delete_relation(db, relation_id, current_user)
    return success(message="删除成功")
