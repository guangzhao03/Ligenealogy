ROLE_MEMBER = "member"
ROLE_EDITOR = "editor"
ROLE_ADMIN = "admin"

ROLE_LABELS = {
    ROLE_MEMBER: "普通族民",
    ROLE_EDITOR: "信息发布员",
    ROLE_ADMIN: "管理员",
}

ROLE_RANK = {
    ROLE_MEMBER: 1,
    ROLE_EDITOR: 2,
    ROLE_ADMIN: 3,
}

VALID_ROLES = frozenset(ROLE_RANK.keys())


def role_at_least(user_role: str, required: str) -> bool:
    return ROLE_RANK.get(user_role, 0) >= ROLE_RANK.get(required, 999)
