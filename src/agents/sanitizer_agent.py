from groq import Groq
from src.config import GROQ_API_KEY, GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)

# --- כאן מוגדר הפרומפט של הסוכן (ההוראות שהוא מקבל) ---
SANITIZER_SYSTEM_PROMPT = """
You are a strict Data Loss Prevention (DLP) text replacer. 
Your ONLY job is to copy the exact text provided by the user, word-for-word, and replace sensitive entities.

CRITICAL RULES:
1. COPY THE ENTIRE INPUT EXACTLY. Do not summarize, truncate, or skip any lines! You must include the user's prompt and the "--- ATTACHED FILE CONTENT ---" header exactly as they appear.
2. Replace PII (names, phone numbers, IDs) with [PII_REDACTED].
3. Replace secrets with [CONFIDENTIAL].
4. Output absolutely nothing else besides the modified text.
"""

def sanitize_prompt(original_text: str, detected_items: list = None) -> str:
    """
    מקבל טקסט נגוע במידע רגיש, שולח למודל ה-AI להלבנה,
    ומחזיר מחרוזת נקייה שבטוחה לשימוש תוך שימוש בתגיות XML לשמירה על הקשר.
    """
    items_to_hide = ", ".join(detected_items) if detected_items else "sensitive data"
    
    # חיבור ההוראות הקבועות עם הפריטים הספציפיים שהמאבחן מצא ותגיות ה-XML
    dynamic_prompt = SANITIZER_SYSTEM_PROMPT + f"\nSpecifically, redact these items: {items_to_hide}\nCRITICAL: Read the text inside the <input> tags. You must output the EXACT SAME TEXT, line by line, from start to finish, replacing only the sensitive data."
    
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": dynamic_prompt},
            # עטיפת הטקסט בתגיות XML כדי שהמודל לא יחתוך חלקים ממנו
            {"role": "user", "content": f"<input>\n{original_text}\n</input>"}
        ],
        temperature=0.0 
    )
    
    clean_text = response.choices[0].message.content.strip()
    
    # הסרת תגיות ה-XML מהתשובה הסופית
    clean_text = clean_text.replace("<input>", "").replace("</input>", "").strip()
    
    return clean_text