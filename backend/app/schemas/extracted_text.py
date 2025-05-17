from datetime import datetime
from pydantic import BaseModel


class ExtractedTextBase(BaseModel):
    page_number: int
    text_content: str


class ExtractedTextCreate(ExtractedTextBase):
    document_id: int


class ExtractedTextResponse(ExtractedTextBase):
    id: int
    document_id: int
    confidence: float | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
