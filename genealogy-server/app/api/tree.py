from fastapi import APIRouter, Query

from app.core.deps import AdminUserDep, DbDep
from app.services import tree_service
from app.utils.response import success

router = APIRouter(prefix="/api/tree", tags=["tree"])


@router.get("/full")
def get_full_tree(
    db: DbDep,
    current_user: AdminUserDep,
    family_id: int = Query(...),
):
    graph = tree_service.get_full_tree(db, family_id, current_user)
    return success(graph.model_dump())


@router.get("/person")
def get_person_tree(
    db: DbDep,
    current_user: AdminUserDep,
    family_id: int = Query(...),
    person_id: int = Query(..., description="指定人物 ID"),
    direction: str = Query(
        default="center",
        description="center=以人为中心, ancestors=向上查祖, descendants=向下查孙, patrilineal=男系世系",
    ),
    up_generations: int = Query(default=5, ge=0, le=30),
    down_generations: int = Query(default=5, ge=0, le=30),
):
    graph = tree_service.get_person_tree(
        db,
        family_id,
        current_user,
        person_id=person_id,
        direction=direction,
        up_generations=up_generations,
        down_generations=down_generations,
    )
    return success(graph.model_dump())


@router.get("/ancestors")
def get_ancestors_tree(
    db: DbDep,
    current_user: AdminUserDep,
    family_id: int = Query(...),
    start_generation: int | None = Query(default=None, ge=1),
    max_generations: int = Query(default=10, ge=1, le=30),
    person_id: int | None = Query(default=None),
):
    graph = tree_service.get_ancestors_tree(
        db,
        family_id,
        current_user,
        start_generation=start_generation or 1,
        max_generations=max_generations,
        person_id=person_id,
    )
    return success(graph.model_dump())


@router.get("/patrilineal")
def get_patrilineal_tree(
    db: DbDep,
    current_user: AdminUserDep,
    family_id: int = Query(...),
    root_person_id: int | None = Query(default=None),
    max_generations: int = Query(default=12, ge=1, le=30),
):
    graph = tree_service.get_patrilineal_tree(
        db,
        family_id,
        current_user,
        root_person_id=root_person_id,
        max_generations=max_generations,
    )
    return success(graph.model_dump())


@router.get("/lineage")
def get_lineage_tree(
    db: DbDep,
    current_user: AdminUserDep,
    family_id: int = Query(...),
    person_id: int = Query(...),
    up_generations: int = Query(default=5, ge=0, le=30),
    down_generations: int = Query(default=5, ge=0, le=30),
):
    graph = tree_service.get_lineage_tree(
        db,
        family_id,
        current_user,
        person_id=person_id,
        up_generations=up_generations,
        down_generations=down_generations,
    )
    return success(graph.model_dump())


@router.get("/descendants")
def get_descendants_tree(
    db: DbDep,
    current_user: AdminUserDep,
    family_id: int = Query(...),
    start_generation: int | None = Query(default=None, ge=1),
    max_generations: int = Query(default=10, ge=1, le=30),
    person_id: int | None = Query(default=None),
):
    graph = tree_service.get_descendants_tree(
        db,
        family_id,
        current_user,
        start_generation=start_generation or 1,
        max_generations=max_generations,
        person_id=person_id,
    )
    return success(graph.model_dump())
