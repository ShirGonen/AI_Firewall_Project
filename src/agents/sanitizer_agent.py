import re
from groq import Groq
from src.config import GROQ_API_KEY, GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)

SANITIZER_SYSTEM_PROMPT = """
You are a strict Data Loss Prevention (DLP) text replacer. 
Your ONLY job is to copy the exact text provided by the user, word-for-word, and replace sensitive entities.

CRITICAL RULES:
1. COPY THE ENTIRE INPUT EXACTLY. Do not summarize, truncate, or skip any lines! You must include the user's prompt and the "--- ATTACHED FILE CONTENT ---" header exactly as they appear.
2. Replace PII (names, phone numbers, IDs) with [PII_REDACTED].
3. Replace secrets with [CONFIDENTIAL].
4. Output absolutely nothing else besides the modified text.
"""

def mask_technical_data(text: str) -> str:
    """
    פונקציית עזר המשתמשת ב-Regex כדי לנקות נתונים טכניים קשיחים (כמו כתובות IP)
    עוד לפני שה-AI בכלל קורא את הטקסט.
    """
    # ביטוי רגולרי לזיהוי כתובות IPv4 (לדוגמה: 192.168.1.1 או 10.0.0.1)
    ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    
    # מחליפים את כל כתובות ה-IP בתגית אבטחה
    masked_text = re.sub(ipv4_pattern, '[IP_REDACTED]', text)
    
    return masked_text

def sanitize_prompt(original_text: str, detected_items: list = None) -> str:
    """
    מקבל טקסט נגוע במידע רגיש, שולח למודל ה-AI להלבנה,
    ומחזיר מחרוזת נקייה שבטוחה לשימוש תוך שימוש בתגיות XML לשמירה על הקשר.
    """
    
    # --- שלב א': ניקוי קשיח טכני (Regex) ---
    # מנקים את כתובות ה-IP לפני שה-AI בכלל רואה את זה
    pre_cleaned_text = mask_technical_data(original_text)
    
    # --- שלב ב': ניקוי חכם (AI) ---
    items_to_hide = ", ".join(detected_items) if detected_items else "sensitive data"
    
    dynamic_prompt = SANITIZER_SYSTEM_PROMPT + f"\nSpecifically, redact these items: {items_to_hide}\nCRITICAL: Read the text inside the <input> tags. You must output the EXACT SAME TEXT, line by line, from start to finish, replacing only the sensitive data."
    
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": dynamic_prompt},
            # שולחים ל-AI את הטקסט שכבר נוקה מכתובות IP!
            {"role": "user", "content": f"<input>\n{pre_cleaned_text}\n</input>"}
        ],
        temperature=0.0 
    )
    
    clean_text = response.choices[0].message.content.strip()
    clean_text = clean_text.replace("<input>", "").replace("</input>", "").strip()
    
    return clean_text