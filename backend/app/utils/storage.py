import os
import shutil
from typing import Optional
from fastapi import UploadFile

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
    
    file_path = os.path.join(UPLOAD_DIR, filename)
    
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
    return file_path
