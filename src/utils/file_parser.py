import os
# אופציונלי: חילוץ מקבצי PDF (דורש התקנה של PyPDF2)
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

def extract_text_from_file(file_path: str) -> str:
    """
    מקבל נתיב לקובץ, קורא אותו ומחזיר את הטקסט מתוכו.
    תומך בקבצי טקסט (TXT, CSV, JSON, MD) וב-PDF (אם הספרייה מותקנת).
    """
    if not os.path.exists(file_path):
        return f"[ERROR] File not found: {file_path}"
        
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    try:
        # טיפול בקבצי טקסט רגילים
        if ext in ['.txt', '.csv', '.json', '.md']:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        # טיפול בקבצי PDF
        elif ext == '.pdf':
            if not PDF_SUPPORT:
                return "[ERROR] PyPDF2 is not installed. Run 'pip install PyPDF2' to read PDFs."
            
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            return text
            
        else:
            return f"[ERROR] Unsupported file type: {ext}"
            
    except Exception as e:
        return f"[ERROR] Failed to read file: {str(e)}"