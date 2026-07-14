from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.family import router as family_router
from app.api.geo_places import router as geo_places_router
from app.api.import_export import router as import_export_router
from app.api.media import router as media_router
from app.api.person import router as person_router
from app.api.public import router as public_router
from app.api.relation import router as relation_router
from app.api.tree import router as tree_router
from app.api.user import router as user_router
from app.core.config import settings
from app.services.media_service import get_upload_root
from app.utils.exceptions import AppException

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(_request: Request, exc: AppException):
    return JSONResponse(
        status_code=200,
        content={"code": exc.code, "message": exc.message, "data": None},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(family_router)
app.include_router(person_router)
app.include_router(relation_router)
app.include_router(tree_router)
app.include_router(public_router)
app.include_router(geo_places_router)
app.include_router(media_router)
app.include_router(import_export_router)

upload_root = get_upload_root()
app.mount("/uploads", StaticFiles(directory=str(upload_root)), name="uploads")
