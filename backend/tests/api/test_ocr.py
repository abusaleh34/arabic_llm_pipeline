import os
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.models.document import Document

client = TestClient(app)

def create_test_pdf(path: str):
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "مرحبا")
    doc.save(path)
    doc.close()


def test_ocr_document(tmp_path):
    test_pdf = tmp_path / "ocr_test.pdf"
    create_test_pdf(str(test_pdf))
    with open(test_pdf, "rb") as f:
        response = client.post("/api/documents/upload", files={"file": (test_pdf.name, f, "application/pdf")})
    assert response.status_code == 200
    doc_id = response.json()["id"]
    response = client.post(f"/api/ocr/{doc_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["page_number"] == 1
    assert "مرحبا" in data[0]["text_content"]
