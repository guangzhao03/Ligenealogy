from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.roles import ROLE_ADMIN, VALID_ROLES
from app.models.user import User
from app.utils.exceptions import BadRequestException, ForbiddenException, NotFoundException


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id.asc())).all())


def update_user_role(db: Session, user_id: int, role: str, actor: User) -> User:
    if role not in VALID_ROLES:
        raise BadRequestException("无效角色，应为 member / editor / admin")

    user = db.get(User, user_id)
    if user is None:
        raise NotFoundException("用户不存在")

    if user.role == ROLE_ADMIN and role != ROLE_ADMIN:
        admin_count = db.scalar(
            select(func.count()).select_from(User).where(User.role == ROLE_ADMIN)
        ) or 0
        if admin_count <= 1:
            raise ForbiddenException("不能取消最后一个管理员")

    user.role = role
    db.commit()
    db.refresh(user)
    return user
