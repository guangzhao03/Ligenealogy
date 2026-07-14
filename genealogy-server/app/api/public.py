from fastapi import APIRouter, Query

from app.core.deps import DbDep, OptionalUserDep
from app.services import public_service
from app.utils.response import success

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/family")
def get_public_family(db: DbDep, optional_user: OptionalUserDep):
    # future: require_viewer if settings.public_require_auth
    public_service.assert_public_access(optional_user)
    return success(public_service.get_family_overview(db))


@router.get("/persons")
def list_public_persons(
    db: DbDep,
    optional_user: OptionalUserDep,
    keyword: str | None = Query(default=None),
    generation: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    public_service.assert_public_access(optional_user)
    payload = public_service.list_persons(
        db,
        keyword=keyword,
        generation=generation,
        page=page,
        page_size=page_size,
    )
    return success(payload.model_dump())


@router.get("/persons/{person_id}/relations")
def get_public_person_relations(person_id: int, db: DbDep, optional_user: OptionalUserDep):
    public_service.assert_public_access(optional_user)
    relations = public_service.get_person_relations(db, person_id)
    return success(relations.model_dump())


@router.get("/persons/{person_id}")
def get_public_person(person_id: int, db: DbDep, optional_user: OptionalUserDep):
    public_service.assert_public_access(optional_user)
    person = public_service.get_person(db, person_id)
    return success(person.model_dump())


@router.get("/tree/full")
def get_public_full_tree(db: DbDep, optional_user: OptionalUserDep):
    public_service.assert_public_access(optional_user)
    graph = public_service.get_full_tree(db)
    return success(graph.model_dump())


@router.get("/tree/patrilineal")
def get_public_patrilineal_tree(
    db: DbDep,
    optional_user: OptionalUserDep,
    root_person_id: int | None = Query(default=None),
    max_generations: int = Query(default=12, ge=1, le=30),
):
    public_service.assert_public_access(optional_user)
    graph = public_service.get_patrilineal_tree(
        db,
        root_person_id=root_person_id,
        max_generations=max_generations,
    )
    return success(graph.model_dump())


@router.get("/tree/lineage")
def get_public_lineage_tree(
    db: DbDep,
    optional_user: OptionalUserDep,
    person_id: int = Query(...),
    up_generations: int = Query(default=5, ge=0, le=30),
    down_generations: int = Query(default=5, ge=0, le=30),
):
    public_service.assert_public_access(optional_user)
    graph = public_service.get_lineage_tree(
        db,
        person_id=person_id,
        up_generations=up_generations,
        down_generations=down_generations,
    )
    return success(graph.model_dump())


@router.get("/geo-places")
def list_public_geo_places(
    db: DbDep,
    optional_user: OptionalUserDep,
    place_type: str | None = Query(default=None),
):
    public_service.assert_public_access(optional_user)
    items = public_service.list_geo_places(db, place_type=place_type)
    return success([item.model_dump() for item in items])


@router.get("/residences")
def list_public_residences(db: DbDep, optional_user: OptionalUserDep):
    public_service.assert_public_access(optional_user)
    items = public_service.list_residences(db)
    return success([item.model_dump() for item in items])


@router.get("/tree/person")
def get_public_person_tree(
    db: DbDep,
    optional_user: OptionalUserDep,
    person_id: int = Query(...),
    direction: str = Query(default="center"),
    up_generations: int = Query(default=5, ge=0, le=30),
    down_generations: int = Query(default=5, ge=0, le=30),
):
    public_service.assert_public_access(optional_user)
    graph = public_service.get_person_tree(
        db,
        person_id=person_id,
        direction=direction,
        up_generations=up_generations,
        down_generations=down_generations,
    )
    return success(graph.model_dump())
