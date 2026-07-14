from pydantic import BaseModel


class TreeNode(BaseModel):
    id: str
    label: str
    name: str
    nickname: str | None = None
    birth_year: int | None = None
    generation: int | None = None
    gender: int = 0
    is_alive: int = 1
    is_main_line: bool = False
    spouse_name: str | None = None
    spouse_nickname: str | None = None


class TreeEdge(BaseModel):
    source: str
    target: str
    relation: str


class TreeGraphResponse(BaseModel):
    nodes: list[TreeNode]
    edges: list[TreeEdge]
    root_id: str | None = None
    root_ids: list[str] = []
    is_forest: bool = False
    max_generation: int | None = None
    start_generation: int | None = None
    focus_person_id: str | None = None


class FamilyStatsResponse(BaseModel):
    person_count: int
    male_count: int
    female_count: int
    min_generation: int | None
    max_generation: int | None
    generation_span: int
