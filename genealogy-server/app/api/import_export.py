from fastapi import APIRouter, File, Form, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.core.deps import AdminUserDep, DbDep
from app.services import import_export_service
from app.utils.response import success

router = APIRouter(tags=["import-export"])


@router.post("/api/import/persons")
async def import_persons(
    db: DbDep,
    current_user: AdminUserDep,
    family_id: int = Form(...),
    file: UploadFile = File(...),
):
    result = await import_export_service.import_persons(
        db, current_user, family_id, file
    )
    message = "导入成功" if not result.errors else "导入失败"
    return success(result.model_dump(), message)


@router.post("/api/import/relations")
async def import_relations(
    db: DbDep,
    current_user: AdminUserDep,
    family_id: int = Form(...),
    file: UploadFile = File(...),
):
    result = await import_export_service.import_relations(
        db, current_user, family_id, file
    )
    message = "导入成功" if not result.errors else "导入失败"
    return success(result.model_dump(), message)


@router.get("/api/export/persons")
def export_persons(
    db: DbDep,
    current_user: AdminUserDep,
    family_id: int = Query(...),
):
    buffer, filename = import_export_service.export_persons(db, current_user, family_id)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/api/export/relations")
def export_relations(
    db: DbDep,
    current_user: AdminUserDep,
    family_id: int = Query(...),
):
    buffer, filename = import_export_service.export_relations(
        db, current_user, family_id
    )
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
