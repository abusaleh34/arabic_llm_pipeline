from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.models.document import DocumentStatus, DocumentType


class DocumentBase(BaseModel):
    name: str


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[DocumentStatus] = None
    file_type: Optional[DocumentType] = None


class DocumentResponse(DocumentBase):
    id: int
    original_filename: str
    file_path: str
    file_size: int
    file_type: DocumentType
    mime_type: str
    page_count: int
    status: DocumentStatus
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class DocumentList(BaseModel):
    items: List[DocumentResponse]
    total: int
