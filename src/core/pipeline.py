import os
from src.agents.assessment_agent import assess_prompt
from src.agents.sanitizer_agent import sanitize_prompt
from src.utils.file_parser import extract_text_from_file

def process_chat_input(user_text: str = "", file_path: str = None) -> dict:
    """
    מנהל את כל תהליך ה-Firewall:
    1. מקבל טקסט ו/או קובץ מהמשתמש.
    2. מאחד אותם למטען (Payload) אחד.
    3. מעביר לסוכן האבחון.
    4. חוסם, מנקה או מאשר - ומחזיר את ההתראות המתאימות.
    """
    
    # --- שלב 1: הכנת המידע (Data Ingestion) ---
    combined_payload = user_text.strip() if user_text else ""
    
    if file_path and os.path.exists(file_path):
        file_content = extract_text_from_file(file_path)
        
        # אם יש גם טקסט וגם קובץ, משרשרים אותם ברור כדי שה-AI יבין את ההקשר
        if combined_payload:
            combined_payload += f"\n\n--- ATTACHED FILE CONTENT ---\n{file_content}"
        else:
            combined_payload = file_content
            
    # אם לא הוזן כלום (לא טקסט ולא קובץ), מחזירים שגיאה
    if not combined_payload:
        return {"status": "ERROR", "message": "No input or file provided."}

    # --- שלב 2: אבחון ה-Firewall (Assessment) ---
    assessment = assess_prompt(combined_payload)
    action = assessment.get("action")
    
    # --- שלב 3: ניתוב, התראות וניקוי (Routing & Sanitization) ---
    if action == "BLOCK":
        return {
            "status": "BLOCKED",
            "user_alert": "🚫 הבקשה נחסמה: זוהה ניסיון לעקיפת אבטחה או הזרקת פקודות זדוניות.",
            "internal_sec_log": assessment
        }
        
    elif action in ["MASK_PII", "DEEP_REDACT"]:
        detected_items = assessment.get("detected_items", [])
        
        # מעבירים את המטען המלא לסוכן הניקוי
        safe_text = sanitize_prompt(combined_payload, detected_items)
        
        return {
            "status": "SANITIZED",
            "user_alert": "🛡️ שים לב: המערכת זיהתה והסתירה מידע ארגוני/אישי רגיש לפני השליחה למודל.",
            "safe_text_for_llm": safe_text
        }
        
    else: # ALLOW
        return {
            "status": "APPROVED",
            "user_alert": None,
            "safe_text_for_llm": combined_payload
        }