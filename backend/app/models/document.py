from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.db.base import Base


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
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    def __repr__(self):
        return f"<Document {self.name}>"
