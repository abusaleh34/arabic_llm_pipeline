import os
import pytest
import shutil
from fastapi.testclient import TestClient
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.api.deps import get_current_user_or_dummy, oauth2_scheme
from app.models.user import User, UserRole


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


TEST_UPLOAD_DIR = "test_uploads"


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_user():
    """
    Create a test user for authentication.
    """
    return User(
        id=1,
        username="test_user",
        email="test@example.com",
        hashed_password="test_password",
        role=UserRole.USER,
        is_active=True
    )


@pytest.fixture(scope="function")
def client(db, test_user):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    async def override_get_current_user_or_dummy():
        return User(
            id=1,
            username="test_user",
            email="test@example.com",
            hashed_password="test_password",
            role=UserRole.USER,
            is_active=True
        )
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_or_dummy] = override_get_current_user_or_dummy
    app.dependency_overrides[oauth2_scheme] = lambda: "test_token"
    
    os.environ["UPLOAD_DIR"] = TEST_UPLOAD_DIR
    os.makedirs(TEST_UPLOAD_DIR, exist_ok=True)
    
    with TestClient(app) as client:
        yield client
    
    if os.path.exists(TEST_UPLOAD_DIR):
        shutil.rmtree(TEST_UPLOAD_DIR)
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_pdf():
    """
    Create a simple test PDF file for testing uploads.
    """
    import fitz  # PyMuPDF
    
    doc = fitz.open()
    page = doc.new_page()
    
    text = "This is a test PDF document for testing uploads."
    page.insert_text((50, 50), text)
    
    test_pdf_path = "test.pdf"
    doc.save(test_pdf_path)
    doc.close()
    
    yield test_pdf_path
    
    if os.path.exists(test_pdf_path):
        os.remove(test_pdf_path)
