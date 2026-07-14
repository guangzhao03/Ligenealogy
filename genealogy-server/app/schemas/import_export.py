from pydantic import BaseModel


class ImportErrorItem(BaseModel):
    row: int
    message: str


class ImportResult(BaseModel):
    success_count: int
    errors: list[ImportErrorItem]
