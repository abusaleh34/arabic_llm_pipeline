import os
import shutil
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus, DocumentType
from app.utils.storage import save_file, delete_file
from app.utils.pdf_utils import get_pdf_info, is_searchable_pdf


class DocumentService:
    def __init__(self, db: Session):
        self.db = db

    async def create_document(self, file: UploadFile, user_id: Optional[int] = None) -> Document:
        """
        Create a new document from an uploaded file.
        """
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        
        file_path = await save_file(file, unique_filename)
        
        file_size = os.path.getsize(file_path)
        
        pdf_info = await get_pdf_info(file_path)
        
        is_searchable = await is_searchable_pdf(file_path)
        file_type = DocumentType.SEARCHABLE if is_searchable else DocumentType.SCANNED
        
        document = Document(
            name=file.filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            mime_type=file.content_type,
            page_count=pdf_info.get("page_count", 0),
            status=DocumentStatus.UPLOADED,
            user_id=user_id
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        return document

    async def get_document(self, document_id: int, user_id: Optional[int] = None) -> Optional[Document]:
        """
        Get a document by ID.
        """
        query = self.db.query(Document).filter(Document.id == document_id)
        
        if user_id is not None:
            query = query.filter(Document.user_id == user_id)
        
        document = query.first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return document

    async def get_documents(self, user_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Document]:
        """
        Get all documents for a user.
        """
        query = self.db.query(Document)
        
        if user_id is not None:
            query = query.filter(Document.user_id == user_id)
        
        return query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

    async def update_document(self, document_id: int, user_id: Optional[int] = None, **kwargs) -> Document:
        """
        Update a document.
        """
        document = await self.get_document(document_id, user_id)
        
        for key, value in kwargs.items():
            if hasattr(document, key):
                setattr(document, key, value)
        
        document.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(document)
        
        return document

    async def delete_document(self, document_id: int, user_id: Optional[int] = None) -> bool:
        """
        Delete a document.
        """
        document = await self.get_document(document_id, user_id)
        
        await delete_file(document.file_path)
        
        self.db.delete(document)
        self.db.commit()
        
        return True

    async def bulk_upload_documents(self, files: List[UploadFile], user_id: Optional[int] = None) -> List[Document]:
        """
        Upload multiple documents at once.
        """
        documents = []
        
        for file in files:
            document = await self.create_document(file, user_id)
            documents.append(document)
        
        return documents
