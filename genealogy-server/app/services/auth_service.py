from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserLogin, UserRegister
from app.utils.exceptions import BadRequestException, ConflictException, UnauthorizedException


from app.core.roles import ROLE_ADMIN, ROLE_MEMBER


def register_user(db: Session, data: UserRegister) -> User:
    existing = db.scalar(select(User).where(User.username == data.username))
    if existing:
        raise ConflictException("用户名已存在")

    # 约定：用户名 admin 注册时自动成为管理员
    role = ROLE_ADMIN if data.username.strip().lower() == "admin" else ROLE_MEMBER

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        nickname=data.nickname or data.username,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, data: UserLogin) -> str:
    user = db.scalar(select(User).where(User.username == data.username))
    if user is None or not verify_password(data.password, user.password_hash):
        raise UnauthorizedException("用户名或密码错误")
    return create_access_token(str(user.id))
