import os
from dotenv import load_dotenv
from groq import Groq

# טעינת מפתח ה-API מקובץ ה-.env שלך
load_dotenv()

# התחברות ל-Groq
client = Groq()

print("Fetching available models from Groq...\n")
try:
    # בקשת רשימת המודלים
    models = client.models.list()
    
    print("✅ Available models for your account:")
    for model in models.data:
        print(f"- {model.id}")
except Exception as e:
    print(f"❌ Error fetching models: {e}")