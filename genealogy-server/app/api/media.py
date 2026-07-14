from fastapi import APIRouter, File, Form, UploadFile

from app.core.deps import AdminUserDep, DbDep
from app.services import media_service
from app.utils.response import success

router = APIRouter(prefix="/api/media", tags=["media"])


@router.post("/upload")
async def upload_media(
    db: DbDep,
    current_user: AdminUserDep,
    person_id: int = Form(...),
    file: UploadFile = File(...),
    is_avatar: bool = Form(default=False),
):
    media = await media_service.upload_media(
        db, current_user, person_id, file, is_avatar=is_avatar
    )
    return success(media.model_dump(), "上传成功")


@router.delete("/{media_id}")
def delete_media(media_id: int, db: DbDep, current_user: AdminUserDep):
    media_service.delete_media(db, media_id, current_user)
    return success(message="删除成功")
