from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.person_relation import PersonRelation
from app.models.user import User
from app.schemas.relation_type import RelationType
from app.schemas.tree import TreeEdge, TreeGraphResponse, TreeNode
from app.services import family_service
from app.utils.exceptions import BadRequestException, NotFoundException

GENDER_MALE = 1
GENDER_FEMALE = 2

PERSON_TREE_DIRECTIONS = frozenset({"center", "ancestors", "descendants", "patrilineal"})


def _format_person_label(person: Person) -> str:
    if person.nickname:
        return f"{person.name}\uff08{person.nickname}\uff09"
    return person.name


def _format_spouse_label(person: Person) -> str:
    if person.nickname:
        return f"{person.name}\uff08{person.nickname}\uff09"
    return person.name


def _person_to_node(
    person: Person,
    *,
    is_main_line: bool = False,
    spouse_name: str | None = None,
    spouse_nickname: str | None = None,
) -> TreeNode:
    return TreeNode(
        id=str(person.id),
        label=_format_person_label(person),
        name=person.name,
        nickname=person.nickname or None,
        birth_year=person.birth_year,
        generation=person.generation,
        gender=person.gender,
        is_alive=person.is_alive,
        is_main_line=is_main_line,
        spouse_name=spouse_name,
        spouse_nickname=spouse_nickname,
    )


def _load_family_graph(db: Session, family_id: int):
    persons = db.scalars(select(Person).where(Person.family_id == family_id)).all()
    relations = db.scalars(
        select(PersonRelation).where(PersonRelation.family_id == family_id)
    ).all()
    person_map = {person.id: person for person in persons}
    return person_map, relations


def _build_relation_maps(relations: list[PersonRelation]):
    parent_of: dict[int, list[int]] = {}
    children_of: dict[int, list[int]] = {}
    spouses_of: dict[int, list[int]] = {}

    for relation in relations:
        if relation.relation_type == RelationType.parent.value:
            parent_of.setdefault(relation.to_person_id, []).append(relation.from_person_id)
            children_of.setdefault(relation.from_person_id, []).append(relation.to_person_id)
        elif relation.relation_type == RelationType.spouse.value:
            spouses_of.setdefault(relation.from_person_id, []).append(relation.to_person_id)
            spouses_of.setdefault(relation.to_person_id, []).append(relation.from_person_id)

    return parent_of, children_of, spouses_of


def _spouse_meta(
    person_id: int,
    person_map: dict[int, Person],
    spouses_of: dict[int, list[int]],
) -> tuple[str | None, str | None]:
    if person_map[person_id].gender != GENDER_MALE:
        return None, None
    for spouse_id in spouses_of.get(person_id, []):
        if spouse_id in person_map:
            spouse = person_map[spouse_id]
            return spouse.name, spouse.nickname or None
    return None, None


def _extend_lineage_with_context(
    person_id: int,
    included_ids: set[int],
    child_parent_link: dict[int, int],
    person_map: dict[int, Person],
    parent_of: dict[int, list[int]],
    children_of: dict[int, list[int]],
    spouses_of: dict[int, list[int]],
    *,
    include_parent_context: bool = True,
) -> None:
    for spouse_id in spouses_of.get(person_id, []):
        if spouse_id in person_map:
            included_ids.add(spouse_id)

    # 向上世代为 0 时不扩展父母/兄弟姐妹，避免「向上 0」仍显示祖先
    if not include_parent_context:
        return

    parent_ids = parent_of.get(person_id, [])
    anchor_parents = []
    male_parent = _pick_male_parent(parent_ids, person_map)
    if male_parent is not None:
        anchor_parents.append(male_parent)
    for parent_id in parent_ids:
        if parent_id not in anchor_parents:
            anchor_parents.append(parent_id)

    for parent_id in anchor_parents:
        if parent_id not in person_map:
            continue
        included_ids.add(parent_id)
        for sibling_id in children_of.get(parent_id, []):
            if sibling_id not in person_map:
                continue
            included_ids.add(sibling_id)
            if sibling_id != person_id:
                child_parent_link[sibling_id] = parent_id


def _collect_spouse_edges(
    included_ids: set[int],
    relations: list[PersonRelation],
) -> list[tuple[int, int, str]]:
    edges: list[tuple[int, int, str]] = []
    seen: set[tuple[int, int]] = set()
    for relation in relations:
        if relation.relation_type != RelationType.spouse.value:
            continue
        a, b = relation.from_person_id, relation.to_person_id
        if a not in included_ids or b not in included_ids:
            continue
        key = (min(a, b), max(a, b))
        if key in seen:
            continue
        seen.add(key)
        edges.append((key[0], key[1], RelationType.spouse.value))
    return edges


def _find_patrilineal_root(person_map: dict[int, Person], parent_of: dict[int, list[int]]) -> int | None:
    males = [person for person in person_map.values() if person.gender == GENDER_MALE]
    if not males:
        return None

    roots = [person for person in males if not parent_of.get(person.id)]
    if not roots:
        roots = males

    roots.sort(key=lambda p: (p.generation or 9999, p.id))
    return roots[0].id


def get_patrilineal_tree(
    db: Session,
    family_id: int,
    current_user: User,
    root_person_id: int | None = None,
    max_generations: int = 12,
) -> TreeGraphResponse:
    family_service.get_family(db, family_id, current_user)
    person_map, relations = _load_family_graph(db, family_id)
    if not person_map:
        return TreeGraphResponse(nodes=[], edges=[], root_id=None, max_generation=None)

    parent_of, children_of, spouses_of = _build_relation_maps(relations)
    root_id = root_person_id or _find_patrilineal_root(person_map, parent_of)
    if root_id is None or root_id not in person_map:
        return TreeGraphResponse(nodes=[], edges=[], root_id=None, max_generation=None)

    included_ids: set[int] = set()
    main_line_ids: set[int] = set()
    walked_males: set[int] = set()
    child_parent_link: dict[int, int] = {}
    unique_edges: list[tuple[int, int, str]] = []
    edge_keys: set[tuple[int, int, str]] = set()

    def add_edge(source_id: int, target_id: int, relation: str) -> None:
        key = (source_id, target_id, relation)
        if key not in edge_keys:
            edge_keys.add(key)
            unique_edges.append(key)

    def link_parent(parent_id: int, child_id: int) -> None:
        current_parent = child_parent_link.get(child_id)
        if current_parent is None:
            child_parent_link[child_id] = parent_id
            return
        if (
            person_map[current_parent].gender != GENDER_MALE
            and person_map[parent_id].gender == GENDER_MALE
        ):
            child_parent_link[child_id] = parent_id

    def include_spouse_meta(person_id: int) -> tuple[str | None, str | None]:
        return _spouse_meta(person_id, person_map, spouses_of)

    root_person = person_map[root_id]
    root_generation = root_person.generation or 1
    generation_limit = root_generation + max_generations - 1

    def walk(person_id: int) -> None:
        person = person_map[person_id]
        if person.generation is not None and person.generation > generation_limit:
            return

        if person.gender == GENDER_MALE:
            if person_id in walked_males:
                return
            walked_males.add(person_id)
            main_line_ids.add(person_id)

        included_ids.add(person_id)

        children = [
            child_id
            for child_id in children_of.get(person_id, [])
            if child_id in person_map
        ]
        children.sort(
            key=lambda child_id: (
                person_map[child_id].gender != GENDER_MALE,
                person_map[child_id].generation or 9999,
                person_map[child_id].birth_year or 9999,
                child_id,
            )
        )

        for child_id in children:
            child = person_map[child_id]
            if child.generation is not None and child.generation > generation_limit:
                continue
            included_ids.add(child_id)
            link_parent(person_id, child_id)
            if child.gender == GENDER_MALE:
                walk(child_id)

    root_person = person_map[root_id]
    if root_person.gender == GENDER_MALE:
        walk(root_id)
    else:
        included_ids.add(root_id)
        for child_id in children_of.get(root_id, []):
            if child_id not in person_map:
                continue
            child = person_map[child_id]
            if child.generation is not None and child.generation > generation_limit:
                continue
            included_ids.add(child_id)
            link_parent(root_id, child_id)
            if child.gender == GENDER_MALE:
                walk(child_id)

    for child_id, parent_id in child_parent_link.items():
        add_edge(parent_id, child_id, RelationType.parent.value)

    nodes: list[TreeNode] = []
    max_gen: int | None = None
    for person_id in included_ids:
        person = person_map[person_id]
        spouse_name, spouse_nickname = include_spouse_meta(person_id)
        if person.generation is not None:
            max_gen = person.generation if max_gen is None else max(max_gen, person.generation)
        nodes.append(
            _person_to_node(
                person,
                is_main_line=person_id in main_line_ids,
                spouse_name=spouse_name,
                spouse_nickname=spouse_nickname,
            )
        )

    edges = [
        TreeEdge(source=str(source), target=str(target), relation=relation)
        for source, target, relation in unique_edges
    ]
    return TreeGraphResponse(
        nodes=nodes,
        edges=edges,
        root_id=str(root_id),
        max_generation=max_gen,
        focus_person_id=str(root_id),
    )


def _pick_male_parent(parent_ids: list[int], person_map: dict[int, Person]) -> int | None:
    males = [parent_id for parent_id in parent_ids if person_map[parent_id].gender == GENDER_MALE]
    if males:
        return males[0]
    return parent_ids[0] if parent_ids else None


def _collect_descendants_forest(
    person_map: dict[int, Person],
    children_of: dict[int, list[int]],
    root_ids: list[int],
    start_generation: int,
    max_generations: int,
) -> tuple[set[int], list[tuple[int, int, str]], dict[int, int]]:
    included_ids: set[int] = set()
    child_parent_link: dict[int, int] = {}
    edges: list[tuple[int, int, str]] = []
    generation_limit = start_generation + max_generations - 1

    def link_parent(parent_id: int, child_id: int) -> None:
        current = child_parent_link.get(child_id)
        if current is None:
            child_parent_link[child_id] = parent_id
            return
        if (
            person_map[current].gender != GENDER_MALE
            and person_map[parent_id].gender == GENDER_MALE
        ):
            child_parent_link[child_id] = parent_id

    def walk(person_id: int) -> None:
        if person_id not in person_map:
            return
        person = person_map[person_id]
        if person.generation is not None and person.generation > generation_limit:
            return
        included_ids.add(person_id)
        for child_id in children_of.get(person_id, []):
            if child_id not in person_map:
                continue
            child = person_map[child_id]
            if child.generation is not None and child.generation > generation_limit:
                continue
            link_parent(person_id, child_id)
            walk(child_id)

    for root_id in root_ids:
        walk(root_id)

    for child_id, parent_id in child_parent_link.items():
        if child_id in included_ids and parent_id in included_ids:
            edges.append((parent_id, child_id, RelationType.parent.value))

    return included_ids, edges, child_parent_link


def _collect_ancestors_forest(
    person_map: dict[int, Person],
    parent_of: dict[int, list[int]],
    anchor_ids: list[int],
    start_generation: int,
    max_generations: int,
) -> tuple[set[int], list[tuple[int, int, str]], dict[int, int]]:
    included_ids: set[int] = set()
    child_parent_link: dict[int, int] = {}
    edges: list[tuple[int, int, str]] = []
    generation_floor = max(1, start_generation - max_generations + 1)

    def walk(person_id: int) -> None:
        if person_id not in person_map:
            return
        person = person_map[person_id]
        if person.generation is not None and person.generation < generation_floor:
            return
        included_ids.add(person_id)
        parent_ids = parent_of.get(person_id, [])
        parent_id = _pick_male_parent(parent_ids, person_map)
        if parent_id is None:
            return
        parent = person_map[parent_id]
        if parent.generation is not None and parent.generation < generation_floor:
            return
        child_parent_link[person_id] = parent_id
        walk(parent_id)

    for anchor_id in anchor_ids:
        walk(anchor_id)

    for child_id, parent_id in child_parent_link.items():
        if child_id in included_ids and parent_id in included_ids:
            edges.append((parent_id, child_id, RelationType.parent.value))

    return included_ids, edges, child_parent_link


def _resolve_generation_roots(
    person_map: dict[int, Person],
    start_generation: int,
    person_id: int | None = None,
) -> tuple[list[int], int]:
    if person_id is not None:
        if person_id not in person_map:
            return [], start_generation
        person = person_map[person_id]
        anchor_generation = person.generation or start_generation
        return [person_id], anchor_generation

    roots = [
        person.id
        for person in person_map.values()
        if person.generation == start_generation
    ]
    roots.sort(key=lambda pid: (person_map[pid].gender != GENDER_MALE, pid))
    return roots, start_generation


def get_descendants_tree(
    db: Session,
    family_id: int,
    current_user: User,
    start_generation: int,
    max_generations: int = 10,
    person_id: int | None = None,
) -> TreeGraphResponse:
    family_service.get_family(db, family_id, current_user)
    person_map, relations = _load_family_graph(db, family_id)
    if not person_map:
        return TreeGraphResponse(
            nodes=[],
            edges=[],
            root_ids=[],
            is_forest=False,
            start_generation=start_generation,
        )

    _, children_of, spouses_of = _build_relation_maps(relations)
    root_ids, anchor_generation = _resolve_generation_roots(
        person_map, start_generation, person_id
    )
    if not root_ids:
        return TreeGraphResponse(
            nodes=[],
            edges=[],
            root_ids=[],
            is_forest=False,
            start_generation=start_generation,
        )

    included_ids, edges_data, _ = _collect_descendants_forest(
        person_map, children_of, root_ids, anchor_generation, max_generations
    )
    edges_data = list(edges_data)
    edges_data.extend(_collect_spouse_edges(included_ids, relations))
    is_forest = len(root_ids) > 1 and person_id is None
    graph = _build_graph(
        db,
        included_ids,
        edges_data,
        person_map=person_map,
        spouses_of=spouses_of,
        focus_person_id=person_id,
    )
    graph.root_ids = [str(root_id) for root_id in root_ids if str(root_id) in {node.id for node in graph.nodes}]
    graph.root_id = graph.root_ids[0] if len(graph.root_ids) == 1 else None
    graph.is_forest = is_forest
    graph.start_generation = anchor_generation
    if person_id is not None:
        graph.focus_person_id = str(person_id)
    return graph


def get_ancestors_tree(
    db: Session,
    family_id: int,
    current_user: User,
    start_generation: int,
    max_generations: int = 10,
    person_id: int | None = None,
) -> TreeGraphResponse:
    family_service.get_family(db, family_id, current_user)
    person_map, relations = _load_family_graph(db, family_id)
    if not person_map:
        return TreeGraphResponse(
            nodes=[],
            edges=[],
            root_ids=[],
            is_forest=False,
            start_generation=start_generation,
        )

    parent_of, _, spouses_of = _build_relation_maps(relations)
    anchor_ids, anchor_generation = _resolve_generation_roots(
        person_map, start_generation, person_id
    )
    if not anchor_ids:
        return TreeGraphResponse(
            nodes=[],
            edges=[],
            root_ids=[],
            is_forest=False,
            start_generation=start_generation,
        )

    included_ids, edges_data, _ = _collect_ancestors_forest(
        person_map, parent_of, anchor_ids, anchor_generation, max_generations
    )
    edges_data = list(edges_data)
    edges_data.extend(_collect_spouse_edges(included_ids, relations))
    top_root_ids = [
        str(person_id_value)
        for person_id_value in included_ids
        if not parent_of.get(person_id_value)
        or _pick_male_parent(parent_of[person_id_value], person_map) not in included_ids
    ]
    is_forest = len(top_root_ids) > 1 or (len(anchor_ids) > 1 and person_id is None)
    graph = _build_graph(
        db,
        included_ids,
        edges_data,
        person_map=person_map,
        spouses_of=spouses_of,
        focus_person_id=person_id,
    )
    graph.root_ids = top_root_ids
    graph.root_id = top_root_ids[0] if len(top_root_ids) == 1 else None
    graph.is_forest = is_forest
    graph.start_generation = anchor_generation
    if person_id is not None:
        graph.focus_person_id = str(person_id)
    return graph


def get_lineage_tree(
    db: Session,
    family_id: int,
    current_user: User,
    person_id: int,
    up_generations: int = 5,
    down_generations: int = 5,
) -> TreeGraphResponse:
    family_service.get_family(db, family_id, current_user)
    person_map, relations = _load_family_graph(db, family_id)
    if person_id not in person_map:
        return TreeGraphResponse(nodes=[], edges=[], root_id=None)

    parent_of, children_of, spouses_of = _build_relation_maps(relations)
    anchor = person_map[person_id]
    anchor_generation = anchor.generation or 1
    up_floor = max(1, anchor_generation - up_generations)
    down_limit = anchor_generation + down_generations

    included_ids: set[int] = set()
    child_parent_link: dict[int, int] = {}

    def link_parent(parent_id: int, child_id: int) -> None:
        current = child_parent_link.get(child_id)
        if current is None:
            child_parent_link[child_id] = parent_id
            return
        if (
            person_map[current].gender != GENDER_MALE
            and person_map[parent_id].gender == GENDER_MALE
        ):
            child_parent_link[child_id] = parent_id

    def walk_up(current_id: int) -> None:
        if current_id not in person_map:
            return
        person = person_map[current_id]
        if person.generation is not None and person.generation < up_floor:
            return
        included_ids.add(current_id)
        parent_ids = parent_of.get(current_id, [])
        parent_id = _pick_male_parent(parent_ids, person_map)
        if parent_id is None:
            return
        parent = person_map[parent_id]
        if parent.generation is not None and parent.generation < up_floor:
            return
        child_parent_link[current_id] = parent_id
        walk_up(parent_id)

    def walk_down(current_id: int) -> None:
        if current_id not in person_map:
            return
        person = person_map[current_id]
        if person.generation is not None and person.generation > down_limit:
            return
        included_ids.add(current_id)
        for child_id in children_of.get(current_id, []):
            if child_id not in person_map:
                continue
            child = person_map[child_id]
            if child.generation is not None and child.generation > down_limit:
                continue
            link_parent(current_id, child_id)
            walk_down(child_id)

    walk_up(person_id)
    walk_down(person_id)
    _extend_lineage_with_context(
        person_id,
        included_ids,
        child_parent_link,
        person_map,
        parent_of,
        children_of,
        spouses_of,
        include_parent_context=up_generations > 0,
    )

    edges_data = [
        (parent_id, child_id, RelationType.parent.value)
        for child_id, parent_id in child_parent_link.items()
        if child_id in included_ids and parent_id in included_ids
    ]
    edges_data.extend(
        _collect_spouse_edges(included_ids, relations)
    )

    nodes: list[TreeNode] = []
    max_gen: int | None = None
    for pid in included_ids:
        person = person_map[pid]
        spouse_name, spouse_nickname = _spouse_meta(pid, person_map, spouses_of)
        if person.generation is not None:
            max_gen = person.generation if max_gen is None else max(max_gen, person.generation)
        nodes.append(
            _person_to_node(
                person,
                is_main_line=pid == person_id or person.gender == GENDER_MALE,
                spouse_name=spouse_name,
                spouse_nickname=spouse_nickname,
            )
        )

    edges = [
        TreeEdge(source=str(source), target=str(target), relation=relation)
        for source, target, relation in edges_data
    ]
    return TreeGraphResponse(
        nodes=nodes,
        edges=edges,
        root_id=str(person_id),
        max_generation=max_gen,
        start_generation=anchor_generation,
        focus_person_id=str(person_id),
    )


def _build_graph(
    db: Session,
    person_ids: set[int],
    edges_data: list[tuple[int, int, str]],
    *,
    person_map: dict[int, Person] | None = None,
    spouses_of: dict[int, list[int]] | None = None,
    focus_person_id: int | None = None,
) -> TreeGraphResponse:
    if not person_ids:
        return TreeGraphResponse(nodes=[], edges=[], root_ids=[], is_forest=False)

    if person_map is None:
        persons = db.scalars(select(Person).where(Person.id.in_(person_ids))).all()
        person_map = {person.id: person for person in persons}
    else:
        persons = [person_map[pid] for pid in person_ids if pid in person_map]

    nodes: list[TreeNode] = []
    for person in persons:
        spouse_name, spouse_nickname = (
            _spouse_meta(person.id, person_map, spouses_of) if spouses_of else (None, None)
        )
        nodes.append(
            _person_to_node(
                person,
                spouse_name=spouse_name,
                spouse_nickname=spouse_nickname,
            )
        )
    edges = [
        TreeEdge(source=str(source), target=str(target), relation=relation)
        for source, target, relation in edges_data
    ]
    max_gen = max((p.generation for p in persons if p.generation is not None), default=None)
    return TreeGraphResponse(
        nodes=nodes,
        edges=edges,
        root_id=None,
        root_ids=[],
        is_forest=False,
        max_generation=max_gen,
        focus_person_id=str(focus_person_id) if focus_person_id is not None else None,
    )


def get_person_tree(
    db: Session,
    family_id: int,
    current_user: User,
    person_id: int,
    direction: str = "center",
    up_generations: int = 5,
    down_generations: int = 5,
) -> TreeGraphResponse:
    if direction not in PERSON_TREE_DIRECTIONS:
        raise BadRequestException(
            f"direction 必须是 {', '.join(sorted(PERSON_TREE_DIRECTIONS))} 之一"
        )

    family_service.get_family(db, family_id, current_user)
    person_map, relations = _load_family_graph(db, family_id)
    if person_id not in person_map:
        raise NotFoundException("指定人物不存在或不属于当前家族")

    person = person_map[person_id]
    anchor_generation = person.generation or 1

    if direction == "patrilineal":
        graph = get_patrilineal_tree(
            db,
            family_id,
            current_user,
            root_person_id=person_id,
            max_generations=down_generations,
        )
        graph.focus_person_id = str(person_id)
        return graph

    if direction == "center":
        return get_lineage_tree(
            db,
            family_id,
            current_user,
            person_id=person_id,
            up_generations=up_generations,
            down_generations=down_generations,
        )

    parent_of, children_of, spouses_of = _build_relation_maps(relations)

    if direction == "ancestors":
        included_ids, edges_data, _ = _collect_ancestors_forest(
            person_map,
            parent_of,
            [person_id],
            anchor_generation,
            up_generations,
        )
        edges_data = list(edges_data)
        edges_data.extend(_collect_spouse_edges(included_ids, relations))
        graph = _build_graph(
            db,
            included_ids,
            edges_data,
            person_map=person_map,
            spouses_of=spouses_of,
            focus_person_id=person_id,
        )
        graph.root_id = str(person_id)
        graph.start_generation = anchor_generation
        return graph

    included_ids, edges_data, _ = _collect_descendants_forest(
        person_map,
        children_of,
        [person_id],
        anchor_generation,
        down_generations,
    )
    edges_data = list(edges_data)
    edges_data.extend(_collect_spouse_edges(included_ids, relations))
    graph = _build_graph(
        db,
        included_ids,
        edges_data,
        person_map=person_map,
        spouses_of=spouses_of,
        focus_person_id=person_id,
    )
    graph.root_id = str(person_id)
    graph.root_ids = [str(person_id)]
    graph.start_generation = anchor_generation
    return graph


def get_full_tree(db: Session, family_id: int, current_user: User) -> TreeGraphResponse:
    family_service.get_family(db, family_id, current_user)

    persons = db.scalars(select(Person).where(Person.family_id == family_id)).all()
    relations = db.scalars(
        select(PersonRelation).where(PersonRelation.family_id == family_id)
    ).all()

    nodes = [_person_to_node(person) for person in persons]
    edges = [
        TreeEdge(
            source=str(relation.from_person_id),
            target=str(relation.to_person_id),
            relation=relation.relation_type,
        )
        for relation in relations
    ]
    max_gen = max((p.generation for p in persons if p.generation is not None), default=None)
    return TreeGraphResponse(
        nodes=nodes,
        edges=edges,
        root_id=None,
        root_ids=[],
        is_forest=False,
        max_generation=max_gen,
    )
