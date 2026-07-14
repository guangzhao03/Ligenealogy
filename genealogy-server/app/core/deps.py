from typing import Annotated, Generator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.roles import ROLE_ADMIN, ROLE_EDITOR, role_at_least
from app.db.session import SessionLocal
from app.models.user import User
from app.utils.exceptions import ForbiddenException, UnauthorizedException

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedException("未提供有效的认证令牌")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        subject = payload.get("sub")
        if subject is None:
            raise UnauthorizedException("令牌无效")
        user_id = int(subject)
    except (JWTError, TypeError, ValueError) as exc:
        raise UnauthorizedException("令牌无效或已过期") from exc

    user = db.get(User, user_id)
    if user is None:
        raise UnauthorizedException("用户不存在")
    return user


def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    """Parse Bearer token if present; invalid/missing token yields anonymous (None)."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        subject = payload.get("sub")
        if subject is None:
            return None
        user = db.get(User, int(subject))
        return user
    except (JWTError, TypeError, ValueError):
        return None


def require_min_role(min_role: str):
    def _checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if not role_at_least(current_user.role, min_role):
            raise ForbiddenException("权限不足")
        return current_user

    return _checker


DbDep = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
OptionalUserDep = Annotated[User | None, Depends(get_optional_user)]
AdminUserDep = Annotated[User, Depends(require_min_role(ROLE_ADMIN))]
EditorUserDep = Annotated[User, Depends(require_min_role(ROLE_EDITOR))]
