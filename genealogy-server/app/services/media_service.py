import logging
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.media import Media
from app.models.user import User
from app.schemas.media import MediaResponse
from app.services import family_service, person_service
from app.utils.exceptions import BadRequestException, NotFoundException

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf",
}
MAX_FILE_SIZE = 10 * 1024 * 1024


def get_upload_root() -> Path:
    root = Path(settings.upload_dir)
    if not root.is_absolute():
        root = Path(__file__).resolve().parent.parent.parent / root
    root.mkdir(parents=True, exist_ok=True)
    return root


def _to_media_response(media: Media) -> MediaResponse:
    url = media.file_path if media.file_path.startswith("/") else f"/{media.file_path}"
    return MediaResponse(
        id=media.id,
        person_id=media.person_id,
        family_id=media.family_id,
        file_name=media.file_name,
        file_path=media.file_path,
        mime_type=media.mime_type,
        file_size=media.file_size,
        url=url.replace("\\", "/"),
        created_at=media.created_at,
    )


def _validate_upload(file: UploadFile, content: bytes) -> None:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise BadRequestException("仅支持 jpg、png、pdf 文件")
    if len(content) > MAX_FILE_SIZE:
        raise BadRequestException("文件大小不能超过 10MB")
    if not content:
        raise BadRequestException("文件不能为空")


async def upload_media(
    db: Session,
    current_user: User,
    person_id: int,
    file: UploadFile,
    is_avatar: bool = False,
) -> MediaResponse:
    person = person_service.get_person(db, person_id, current_user)
    content = await file.read()
    _validate_upload(file, content)

    ext = ALLOWED_MIME_TYPES[file.content_type]
    stored_name = f"{uuid.uuid4().hex}{ext}"
    relative_dir = Path(str(person.family_id)) / str(person.id)
    upload_root = get_upload_root()
    target_dir = upload_root / relative_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / stored_name
    target_path.write_bytes(content)

    relative_path = relative_dir / stored_name
    file_path = f"uploads/{relative_path.as_posix()}"

    media = Media(
        person_id=person.id,
        family_id=person.family_id,
        file_name=file.filename or stored_name,
        file_path=file_path,
        mime_type=file.content_type,
        file_size=len(content),
    )
    db.add(media)

    if is_avatar and file.content_type.startswith("image/"):
        person.avatar_url = f"/{file_path}"

    db.commit()
    db.refresh(media)
    return _to_media_response(media)


def list_person_media(
    db: Session, person_id: int, current_user: User
) -> list[MediaResponse]:
    person = person_service.get_person(db, person_id, current_user)
    items = db.scalars(
        select(Media)
        .where(Media.person_id == person.id)
        .order_by(Media.id.desc())
    ).all()
    return [_to_media_response(item) for item in items]


def _disk_path_from_media(file_path: str) -> Path:
    relative = file_path.removeprefix("uploads/").lstrip("/")
    return get_upload_root() / relative


def delete_media(db: Session, media_id: int, current_user: User) -> None:
    media = db.get(Media, media_id)
    if media is None:
        raise NotFoundException("附件不存在")

    family_service.get_family(db, media.family_id, current_user)
    disk_path = _disk_path_from_media(media.file_path)

    db.delete(media)
    db.commit()

    try:
        if disk_path.exists():
            disk_path.unlink()
    except OSError as exc:
        logger.warning("删除磁盘文件失败: %s, error=%s", disk_path, exc)


def delete_person_media(db: Session, person_id: int) -> list[Path]:
    items = db.scalars(select(Media).where(Media.person_id == person_id)).all()
    disk_paths = [_disk_path_from_media(item.file_path) for item in items]
    for item in items:
        db.delete(item)
    return disk_paths
