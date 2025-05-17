from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class ExtractedText(Base):
    __tablename__ = "extracted_texts"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))
    text_content = Column(Text)
    page_number = Column(Integer)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    document = relationship("Document", back_populates="extracted_texts")

    def __repr__(self):
        return f"<ExtractedText doc={self.document_id} page={self.page_number}>"
