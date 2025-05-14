# Phase 1: Data Upload and Management - Implementation Plan

This document provides a detailed implementation plan for Phase 1 of the Arabic PDF Processing and LLM Training Platform.

## Overview

Phase 1 focuses on developing a user-friendly web interface for secure uploading of PDF files (both scanned and searchable), supporting bulk uploads, implementing validation, designing secure storage solutions, and providing functionalities for managing uploaded datasets.

## Backend Implementation

### Database Models

**Document Model (`backend/models/document.py`)**

```python
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship

from backend.db.base import Base


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class DocumentType(str, Enum):
    SCANNED = "scanned"
    SEARCHABLE = "searchable"
    UNKNOWN = "unknown"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    original_filename = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)  # Size in bytes
    file_type = Column(SQLEnum(DocumentType), default=DocumentType.UNKNOWN)
    mime_type = Column(String)
    page_count = Column(Integer, default=0)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADED)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="documents")
    extracted_texts = relationship("ExtractedText", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document {self.name}>"
```

### Services

**Document Service (`backend/services/upload/document_service.py`)**

```python
import os
import shutil
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from backend.models.document import Document, DocumentStatus, DocumentType
from backend.utils.storage import save_file, delete_file
from backend.utils.pdf_utils import get_pdf_info


class DocumentService:
    def __init__(self, db: Session):
        self.db = db

    async def create_document(self, file: UploadFile, user_id: int) -> Document:
        """
        Create a new document from an uploaded file.
        """
        # Validate file
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Generate a unique filename
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        
        # Save file to storage
        file_path = await save_file(file, unique_filename)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        
        # Get PDF info
        pdf_info = await get_pdf_info(file_path)
        
        # Create document record
        document = Document(
            name=file.filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type=DocumentType.UNKNOWN,  # Will be determined during OCR phase
            mime_type=file.content_type,
            page_count=pdf_info.get("page_count", 0),
            status=DocumentStatus.UPLOADED,
            user_id=user_id
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        return document

    async def get_document(self, document_id: int, user_id: int) -> Optional[Document]:
        """
        Get a document by ID.
        """
        document = self.db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == user_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return document

    async def get_documents(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Document]:
        """
        Get all documents for a user.
        """
        return self.db.query(Document).filter(
            Document.user_id == user_id
        ).offset(skip).limit(limit).all()

    async def update_document(self, document_id: int, user_id: int, **kwargs) -> Document:
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

    async def delete_document(self, document_id: int, user_id: int) -> bool:
        """
        Delete a document.
        """
        document = await self.get_document(document_id, user_id)
        
        # Delete file from storage
        await delete_file(document.file_path)
        
        # Delete document record
        self.db.delete(document)
        self.db.commit()
        
        return True

    async def bulk_upload_documents(self, files: List[UploadFile], user_id: int) -> List[Document]:
        """
        Upload multiple documents at once.
        """
        documents = []
        
        for file in files:
            document = await self.create_document(file, user_id)
            documents.append(document)
        
        return documents
```

**Storage Utilities (`backend/utils/storage.py`)**

```python
import os
import shutil
from typing import Optional
from fastapi import UploadFile

# Configuration
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")


async def ensure_upload_dir():
    """
    Ensure the upload directory exists.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)


async def save_file(file: UploadFile, filename: str) -> str:
    """
    Save an uploaded file to storage.
    """
    await ensure_upload_dir()
    
    # Create user directory if it doesn't exist
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return file_path


async def delete_file(file_path: str) -> bool:
    """
    Delete a file from storage.
    """
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False


async def get_file_url(file_path: str) -> str:
    """
    Get the URL for a file.
    """
    # In a production environment, this would generate a signed URL
    # For local development, we'll just return the file path
    return file_path
```

**PDF Utilities (`backend/utils/pdf_utils.py`)**

```python
import fitz  # PyMuPDF
from typing import Dict, Any


async def get_pdf_info(file_path: str) -> Dict[str, Any]:
    """
    Get information about a PDF file.
    """
    try:
        doc = fitz.open(file_path)
        info = {
            "page_count": len(doc),
            "metadata": doc.metadata,
            "is_encrypted": doc.is_encrypted,
        }
        doc.close()
        return info
    except Exception as e:
        return {
            "page_count": 0,
            "error": str(e)
        }


async def is_searchable_pdf(file_path: str) -> bool:
    """
    Check if a PDF is searchable (has text layer).
    """
    try:
        doc = fitz.open(file_path)
        
        # Check a few pages for text
        max_pages_to_check = min(5, len(doc))
        for page_num in range(max_pages_to_check):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                doc.close()
                return True
        
        doc.close()
        return False
    except Exception:
        return False
```

### API Routes

**Document API (`backend/api/routes/document.py`)**

```python
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.models.document import Document
from backend.services.upload.document_service import DocumentService
from backend.api.deps import get_current_user
from backend.schemas.document import DocumentCreate, DocumentResponse, DocumentList

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
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
    current_user = Depends(get_current_user)
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
    current_user = Depends(get_current_user)
):
    """
    Get a document by ID.
    """
    document_service = DocumentService(db)
    document = await document_service.get_document(document_id, current_user.id)
    return document


@router.get("/", response_model=DocumentList)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List all documents for the current user.
    """
    document_service = DocumentService(db)
    documents = await document_service.get_documents(current_user.id, skip, limit)
    return {"items": documents, "total": len(documents)}


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Delete a document.
    """
    document_service = DocumentService(db)
    success = await document_service.delete_document(document_id, current_user.id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete document")
    return {"success": True}
```

## Frontend Implementation

### API Service

**Document API Service (`frontend/src/services/api/documentService.ts`)**

```typescript
import axios from 'axios';
import { API_URL } from '../config';

const API_ENDPOINT = `${API_URL}/api/documents`;

export interface Document {
  id: number;
  name: string;
  file_path: string;
  file_size: number;
  file_type: 'scanned' | 'searchable' | 'unknown';
  page_count: number;
  status: 'uploaded' | 'processing' | 'processed' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  items: Document[];
  total: number;
}

const documentService = {
  // Upload a single document
  uploadDocument: async (file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(`${API_ENDPOINT}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },
  
  // Upload multiple documents
  bulkUploadDocuments: async (files: File[]): Promise<Document[]> => {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    
    const response = await axios.post(`${API_ENDPOINT}/bulk-upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },
  
  // Get a document by ID
  getDocument: async (id: number): Promise<Document> => {
    const response = await axios.get(`${API_ENDPOINT}/${id}`);
    return response.data;
  },
  
  // List all documents
  listDocuments: async (skip = 0, limit = 100): Promise<DocumentListResponse> => {
    const response = await axios.get(`${API_ENDPOINT}?skip=${skip}&limit=${limit}`);
    return response.data;
  },
  
  // Delete a document
  deleteDocument: async (id: number): Promise<boolean> => {
    const response = await axios.delete(`${API_ENDPOINT}/${id}`);
    return response.data.success;
  },
};

export default documentService;
```

### Components

**File Uploader Component (`frontend/src/components/upload/FileUploader.tsx`)**

```tsx
import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import documentService from '../../services/api/documentService';

interface FileUploaderProps {
  onUploadComplete: (success: boolean) => void;
  multiple?: boolean;
}

const FileUploader: React.FC<FileUploaderProps> = ({ 
  onUploadComplete, 
  multiple = false 
}) => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    // Validate files
    const invalidFiles = acceptedFiles.filter(
      file => file.type !== 'application/pdf'
    );

    if (invalidFiles.length > 0) {
      setError('Only PDF files are allowed');
      return;
    }

    setUploading(true);
    setError(null);
    
    try {
      if (multiple) {
        await documentService.bulkUploadDocuments(acceptedFiles);
      } else {
        await documentService.uploadDocument(acceptedFiles[0]);
      }
      
      onUploadComplete(true);
    } catch (err) {
      console.error('Upload error:', err);
      setError('Failed to upload file(s). Please try again.');
      onUploadComplete(false);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  }, [multiple, onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple
  });

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'
        }`}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center justify-center space-y-2">
          <svg
            className="w-12 h-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          
          <p className="text-lg font-medium text-gray-700">
            {isDragActive
              ? 'Drop the files here...'
              : multiple
              ? 'Drag & drop PDF files here, or click to select files'
              : 'Drag & drop a PDF file here, or click to select a file'}
          </p>
          
          <p className="text-sm text-gray-500">
            Only PDF files are supported
          </p>
        </div>
      </div>

      {uploading && (
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-blue-600 h-2.5 rounded-full"
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-600 mt-1">Uploading...</p>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-md">
          {error}
        </div>
      )}
    </div>
  );
};

export default FileUploader;
```

**Document List Component (`frontend/src/components/upload/DocumentList.tsx`)**

```tsx
import React, { useState, useEffect } from 'react';
import documentService, { Document } from '../../services/api/documentService';

interface DocumentListProps {
  onDocumentSelect?: (document: Document) => void;
  refreshTrigger?: number;
}

const DocumentList: React.FC<DocumentListProps> = ({ 
  onDocumentSelect,
  refreshTrigger = 0
}) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const limit = 10;

  const loadDocuments = async (reset = false) => {
    try {
      setLoading(true);
      setError(null);
      
      const newPage = reset ? 0 : page;
      const response = await documentService.listDocuments(newPage * limit, limit);
      
      if (reset) {
        setDocuments(response.items);
      } else {
        setDocuments(prev => [...prev, ...response.items]);
      }
      
      setHasMore(response.items.length === limit);
      if (!reset) {
        setPage(prev => prev + 1);
      } else {
        setPage(1);
      }
    } catch (err) {
      console.error('Error loading documents:', err);
      setError('Failed to load documents. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments(true);
  }, [refreshTrigger]);

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }
    
    try {
      await documentService.deleteDocument(id);
      setDocuments(prev => prev.filter(doc => doc.id !== id));
    } catch (err) {
      console.error('Error deleting document:', err);
      alert('Failed to delete document. Please try again.');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusBadgeColor = (status: string): string => {
    switch (status) {
      case 'uploaded':
        return 'bg-blue-100 text-blue-800';
      case 'processing':
        return 'bg-yellow-100 text-yellow-800';
      case 'processed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="w-full">
      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-md">
          {error}
        </div>
      )}

      <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
        <table className="min-w-full divide-y divide-gray-300">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                Name
              </th>
              <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                Size
              </th>
              <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                Pages
              </th>
              <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                Type
              </th>
              <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                Status
              </th>
              <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                Uploaded
              </th>
              <th scope="col" className="relative px-3 py-3.5">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {documents.length === 0 && !loading ? (
              <tr>
                <td colSpan={7} className="px-3 py-4 text-sm text-gray-500 text-center">
                  No documents found. Upload some documents to get started.
                </td>
              </tr>
            ) : (
              documents.map(doc => (
                <tr 
                  key={doc.id} 
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => onDocumentSelect && onDocumentSelect(doc)}
                >
                  <td className="whitespace-nowrap px-3 py-4 text-sm font-medium text-gray-900">
                    {doc.name}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                    {formatFileSize(doc.file_size)}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                    {doc.page_count}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500 capitalize">
                    {doc.file_type}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm">
                    <span className={`inline-flex rounded-full px-2 text-xs font-semibold leading-5 ${getStatusBadgeColor(doc.status)} capitalize`}>
                      {doc.status}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-right">
                    <button
                      onClick={(e) => handleDelete(doc.id, e)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {loading && (
        <div className="flex justify-center my-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      )}

      {hasMore && !loading && (
        <div className="flex justify-center mt-4">
          <button
            onClick={() => loadDocuments()}
            className="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Load More
          </button>
        </div>
      )}
    </div>
  );
};

export default DocumentList;
```

### Pages

**Upload Page (`frontend/src/pages/upload/UploadPage.tsx`)**

```tsx
import React, { useState } from 'react';
import FileUploader from '../../components/upload/FileUploader';
import DocumentList from '../../components/upload/DocumentList';
import { Document } from '../../services/api/documentService';

const UploadPage: React.FC = () => {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [uploadMode, setUploadMode] = useState<'single' | 'bulk'>('single');

  const handleUploadComplete = (success: boolean) => {
    if (success) {
      // Refresh the document list
      setRefreshTrigger(prev => prev + 1);
    }
  };

  const handleDocumentSelect = (document: Document) => {
    setSelectedDocument(document);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Document Upload</h1>
        <p className="text-gray-600">
          Upload PDF documents for processing. Both scanned and searchable PDFs are supported.
        </p>
      </div>

      <div className="bg-white shadow rounded-lg p-6 mb-8">
        <div className="mb-4">
          <div className="flex space-x-4 mb-4">
            <button
              className={`px-4 py-2 rounded-md ${
                uploadMode === 'single'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
              onClick={() => setUploadMode('single')}
            >
              Single Upload
            </button>
            <button
              className={`px-4 py-2 rounded-md ${
                uploadMode === 'bulk'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
              onClick={() => setUploadMode('bulk')}
            >
              Bulk Upload
            </button>
          </div>
          
          <FileUploader 
            onUploadComplete={handleUploadComplete} 
            multiple={uploadMode === 'bulk'} 
          />
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Documents</h2>
        <DocumentList 
          onDocumentSelect={handleDocumentSelect} 
          refreshTrigger={refreshTrigger} 
        />
      </div>

      {selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Document Details
                </h3>
                <button
                  onClick={() => setSelectedDocument(null)}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <span className="sr-only">Close</span>
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-500">Name</h4>
                  <p className="mt-1">{selectedDocument.name}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">File Type</h4>
                    <p className="mt-1 capitalize">{selectedDocument.file_type}</p>
                  </div>
                  
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">Status</h4>
                    <p className="mt-1 capitalize">{selectedDocument.status}</p>
                  </div>
                  
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">Pages</h4>
                    <p className="mt-1">{selectedDocument.page_count}</p>
                  </div>
                  
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">Uploaded</h4>
                    <p className="mt-1">{new Date(selectedDocument.created_at).toLocaleString()}</p>
                  </div>
                </div>
                
                <div className="pt-4 flex justify-end">
                  <button
                    onClick={() => setSelectedDocument(null)}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadPage;
```

## Testing Strategy

### Backend Tests

1. **Unit Tests**
   - Test document service methods
   - Test storage utilities
   - Test PDF utilities

2. **API Tests**
   - Test document upload endpoints
   - Test document retrieval endpoints
   - Test document deletion endpoints

### Frontend Tests

1. **Component Tests**
   - Test FileUploader component
   - Test DocumentList component

2. **Integration Tests**
   - Test upload workflow
   - Test document management workflow

## Deployment Considerations

1. **Storage Configuration**
   - Configure storage backend (local filesystem, S3, etc.)
   - Set up appropriate permissions

2. **Database Setup**
   - Create necessary database tables
   - Set up indexes for performance

3. **Security**
   - Implement file validation
   - Set up authentication and authorization
   - Configure CORS

## Next Steps

After implementing Phase 1, the following steps should be taken:

1. **Testing**
   - Run unit tests
   - Perform integration tests
   - Conduct user acceptance testing

2. **Documentation**
   - Update API documentation
   - Create user guide for the upload functionality

3. **Preparation for Phase 2**
   - Set up OCR infrastructure
   - Design text extraction workflows
