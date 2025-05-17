import fitz
from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentType, DocumentStatus
from app.models.extracted_text import ExtractedText
from app.utils.pdf_utils import is_searchable_pdf

try:
    import pytesseract
    from PIL import Image
except Exception:  # pragma: no cover
    pytesseract = None  # type: ignore
    Image = None  # type: ignore


class OCRService:
    def __init__(self, db: Session):
        self.db = db

    async def process_document(self, document_id: int, user_id: int) -> List[ExtractedText]:
        document = (
            self.db.query(Document)
            .filter(Document.id == document_id, Document.user_id == user_id)
            .first()
        )
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        file_path = document.file_path
        is_searchable = await is_searchable_pdf(file_path)

        extracted_items: List[ExtractedText] = []
        doc = fitz.open(file_path)

        for page_number in range(len(doc)):
            page = doc[page_number]
            text = page.get_text()
            if not text and not is_searchable and pytesseract and Image:
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(img, lang="ara")

            extracted = ExtractedText(
                document_id=document.id,
                page_number=page_number + 1,
                text_content=text,
                confidence=None,
            )
            self.db.add(extracted)
            extracted_items.append(extracted)

        document.status = DocumentStatus.PROCESSED
        document.file_type = DocumentType.SEARCHABLE if is_searchable else DocumentType.SCANNED
        self.db.commit()

        for item in extracted_items:
            self.db.refresh(item)

        return extracted_items
