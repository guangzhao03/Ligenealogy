from datetime import datetime

from pydantic import BaseModel


class MediaResponse(BaseModel):
    id: int
    person_id: int
    family_id: int
    file_name: str
    file_path: str
    mime_type: str
    file_size: int
    url: str
    created_at: datetime

    model_config = {"from_attributes": True}
