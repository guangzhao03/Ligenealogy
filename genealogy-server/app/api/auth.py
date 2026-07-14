from fastapi import APIRouter

from app.core.deps import CurrentUserDep, DbDep
from app.schemas.user import TokenResponse, UserLogin, UserRegister, UserResponse
from app.services.auth_service import login_user, register_user
from app.utils.response import success

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
def register(data: UserRegister, db: DbDep):
    user = register_user(db, data)
    return success(UserResponse.model_validate(user).model_dump(), "注册成功")


@router.post("/login")
def login(data: UserLogin, db: DbDep):
    token = login_user(db, data)
    return success(TokenResponse(access_token=token).model_dump(), "登录成功")


@router.get("/me")
def me(current_user: CurrentUserDep):
    return success(UserResponse.model_validate(current_user).model_dump())
