import fitz  # PyMuPDF
import sys

def create_test_pdf(filename, text):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    doc.save(filename)
    doc.close()
    print(f"Created test PDF: {filename}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        filename = sys.argv[1]
        text = sys.argv[2]
        create_test_pdf(filename, text)
    else:
        create_test_pdf("test_document.pdf", "This is a test PDF document for Arabic PDF Training Platform.")
