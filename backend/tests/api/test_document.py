import os
import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus, DocumentType


def test_upload_document(client: TestClient, test_pdf: str):
    """
    Test uploading a single document.
    """
    with open(test_pdf, "rb") as f:
        response = client.post(
            "/api/documents/upload",
            files={"file": (os.path.basename(test_pdf), f, "application/pdf")}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "id" in data
    assert data["name"] == os.path.basename(test_pdf)
    assert data["file_type"] in ["scanned", "searchable"]
    assert data["status"] == "uploaded"
    assert data["page_count"] > 0
    assert data["file_size"] > 0


def test_upload_invalid_file_type(client: TestClient):
    """
    Test uploading a file with an invalid type.
    """
    with open("test.txt", "w") as f:
        f.write("This is a test file.")
    
    with open("test.txt", "rb") as f:
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", f, "text/plain")}
        )
    
    assert response.status_code == 400
    assert "Only PDF files are allowed" in response.json()["detail"]
    
    os.remove("test.txt")


def test_bulk_upload_documents(client: TestClient, test_pdf: str):
    """
    Test uploading multiple documents at once.
    """
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "This is a second test PDF document.")
    test_pdf2 = "test2.pdf"
    doc.save(test_pdf2)
    doc.close()
    
    with open(test_pdf, "rb") as f1, open(test_pdf2, "rb") as f2:
        response = client.post(
            "/api/documents/bulk-upload",
            files=[
                ("files", (os.path.basename(test_pdf), f1, "application/pdf")),
                ("files", (os.path.basename(test_pdf2), f2, "application/pdf"))
            ]
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 2
    assert all("id" in doc for doc in data)
    assert all(doc["status"] == "uploaded" for doc in data)
    
    os.remove(test_pdf2)


def test_get_document(client: TestClient, test_pdf: str, db: Session):
    """
    Test getting a document by ID.
    """
    with open(test_pdf, "rb") as f:
        response = client.post(
            "/api/documents/upload",
            files={"file": (os.path.basename(test_pdf), f, "application/pdf")}
        )
    
    upload_data = response.json()
    document_id = upload_data["id"]
    
    response = client.get(f"/api/documents/{document_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == document_id
    assert data["name"] == os.path.basename(test_pdf)
    assert data["status"] == "uploaded"


def test_get_nonexistent_document(client: TestClient):
    """
    Test getting a document that doesn't exist.
    """
    response = client.get("/api/documents/999")
    
    assert response.status_code == 404
    assert "Document not found" in response.json()["detail"]


def test_list_documents(client: TestClient, test_pdf: str):
    """
    Test listing all documents.
    """
    with open(test_pdf, "rb") as f:
        client.post(
            "/api/documents/upload",
            files={"file": (os.path.basename(test_pdf), f, "application/pdf")}
        )
    
    response = client.get("/api/documents/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "items" in data
    assert "total" in data
    assert data["total"] > 0
    assert len(data["items"]) > 0
    assert data["items"][0]["name"] == os.path.basename(test_pdf)


def test_update_document(client: TestClient, test_pdf: str):
    """
    Test updating a document.
    """
    with open(test_pdf, "rb") as f:
        response = client.post(
            "/api/documents/upload",
            files={"file": (os.path.basename(test_pdf), f, "application/pdf")}
        )
    
    upload_data = response.json()
    document_id = upload_data["id"]
    
    new_name = "Updated Test Document.pdf"
    response = client.put(
        f"/api/documents/{document_id}",
        json={"name": new_name}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == document_id
    assert data["name"] == new_name


def test_delete_document(client: TestClient, test_pdf: str):
    """
    Test deleting a document.
    """
    with open(test_pdf, "rb") as f:
        response = client.post(
            "/api/documents/upload",
            files={"file": (os.path.basename(test_pdf), f, "application/pdf")}
        )
    
    upload_data = response.json()
    document_id = upload_data["id"]
    
    response = client.delete(f"/api/documents/{document_id}")
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    response = client.get(f"/api/documents/{document_id}")
    assert response.status_code == 404


def test_pagination(client: TestClient, test_pdf: str):
    """
    Test document listing pagination.
    """
    for i in range(3):
        with open(test_pdf, "rb") as f:
            client.post(
                "/api/documents/upload",
                files={"file": (f"test_{i}.pdf", f, "application/pdf")}
            )
    
    response = client.get("/api/documents/?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    
    response = client.get("/api/documents/?skip=1&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    
    response_first = client.get("/api/documents/?limit=1")
    first_doc_id = response_first.json()["items"][0]["id"]
    assert data["items"][0]["id"] != first_doc_id
