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
