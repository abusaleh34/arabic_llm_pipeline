import fitz
import os

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    arabic_support = True
except ImportError:
    arabic_support = False
    print("Arabic reshaper not installed. Installing required packages...")
    os.system("pip install arabic-reshaper python-bidi")
    import arabic_reshaper
    from bidi.algorithm import get_display

def create_arabic_test_pdfs():
    # Create Arabic test PDF
    doc = fitz.open()
    page = doc.new_page()

    # Arabic text samples
    arabic_text1 = 'هذا مستند اختبار باللغة العربية'
    arabic_text2 = 'يمكن استخدام هذا المستند لاختبار منصة معالجة ملفات PDF العربية'
    arabic_text3 = 'النص العربي يكتب من اليمين إلى اليسار'

    # Reshape and reorder Arabic text for proper display
    reshaped_text1 = arabic_reshaper.reshape(arabic_text1)
    bidi_text1 = get_display(reshaped_text1)
    reshaped_text2 = arabic_reshaper.reshape(arabic_text2)
    bidi_text2 = get_display(reshaped_text2)
    reshaped_text3 = arabic_reshaper.reshape(arabic_text3)
    bidi_text3 = get_display(reshaped_text3)

    # Add text to PDF
    page.insert_text((50, 50), bidi_text1, fontsize=12)
    page.insert_text((50, 100), bidi_text2, fontsize=12)
    page.insert_text((50, 150), bidi_text3, fontsize=12)

    # Save PDF
    doc.save('arabic_test_document.pdf')
    doc.close()
    print('Created Arabic test PDF: arabic_test_document.pdf')

    # Create a second Arabic test PDF (simulating scanned document)
    doc2 = fitz.open()
    page2 = doc2.new_page()

    # Add more Arabic text
    arabic_text4 = 'هذا مستند عربي ثان لاختبار التحميل المتعدد'
    arabic_text5 = 'يحتوي هذا المستند على نص عربي مختلف'

    # Reshape and reorder
    reshaped_text4 = arabic_reshaper.reshape(arabic_text4)
    bidi_text4 = get_display(reshaped_text4)
    reshaped_text5 = arabic_reshaper.reshape(arabic_text5)
    bidi_text5 = get_display(reshaped_text5)

    # Add text to PDF
    page2.insert_text((50, 50), bidi_text4, fontsize=12)
    page2.insert_text((50, 100), bidi_text5, fontsize=12)

    # Save PDF
    doc2.save('arabic_test_document2.pdf')
    doc2.close()
    print('Created Arabic test PDF: arabic_test_document2.pdf')

if __name__ == "__main__":
    create_arabic_test_pdfs()
