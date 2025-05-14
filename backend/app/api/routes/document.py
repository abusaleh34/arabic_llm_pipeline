from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.services.upload.document_service import DocumentService
from app.api.deps import get_current_user_or_dummy
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentList, DocumentUpdate

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_or_dummy)
):
    """
    Upload a single document.
    """
    document_service = DocumentService(db)
    document = await document_service.create_document(file, current_user.id)
    return document


@router.post("/bulk-upload", response_model=List[DocumentResponse])
async def bulk_upload_documents(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_or_dummy)
):
    """
    Upload multiple documents at once.
    """
    document_service = DocumentService(db)
    documents = await document_service.bulk_upload_documents(files, current_user.id)
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_or_dummy)
):
    """
    Get a document by ID.
    """
    document_service = DocumentService(db)
    document = await document_service.get_document(document_id, current_user.id)
    return document


@router.get("/", response_model=DocumentList)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_or_dummy)
):
    """
    List all documents for the current user.
    """
    document_service = DocumentService(db)
    documents = await document_service.get_documents(current_user.id, skip, limit)
    total = len(documents)  # In a real app, this would be a separate count query
    return {"items": documents, "total": total}


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_or_dummy)
):
    """
    Update a document.
    """
    document_service = DocumentService(db)
    document = await document_service.update_document(
        document_id, 
        current_user.id, 
        **document_update.dict(exclude_unset=True)
    )
    return document


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_or_dummy)
):
    """
    Delete a document.
    """
    document_service = DocumentService(db)
    success = await document_service.delete_document(document_id, current_user.id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete document")
    return {"success": True}
