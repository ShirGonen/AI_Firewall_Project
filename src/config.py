import os
from dotenv import load_dotenv

# טעינת המשתנים מתוך קובץ ה-.env
load_dotenv()

# שליפת מפתח ה-API של Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# הגדרת המודל שנעבוד איתו ב-Groq
GROQ_MODEL = "llama-3.3-70b-versatile"

# בדיקה קטנה ששרת האפליקציה לא יעלה בלי מפתח
if not GROQ_API_KEY:
    raise ValueError("Missing GROQ_API_KEY in .env file!")