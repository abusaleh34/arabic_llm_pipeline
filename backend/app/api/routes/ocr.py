from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user_or_dummy
from app.schemas.extracted_text import ExtractedTextResponse
from app.services.ocr.ocr_service import OCRService

router = APIRouter()


@router.post("/{document_id}", response_model=List[ExtractedTextResponse])
async def ocr_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_or_dummy),
):
    service = OCRService(db)
    result = await service.process_document(document_id, current_user.id)
    return result
