import os
import json
from src.core.pipeline import process_chat_input

def test_full_pipeline():
    print("=== 🚀 Testing the Complete AI Firewall Pipeline ===\n")
    
    # 1. ניצור קובץ זמני שמדמה דוח שהעובד צירף (עם מידע רגיש)
    fake_file_path = "temp_secret_report.txt"
    with open(fake_file_path, "w", encoding="utf-8") as f:
        f.write("CONFIDENTIAL: The CEO's private phone number is 050-1234567.")

    # 2. זה הטקסט שהעובד הקליד בתיבת הצ'אט
    user_typed_message = "Please summarize the attached report and translate it to Hebrew."
    
    print(f"💬 User Typed: {user_typed_message}")
    print(f"📎 Attached File: {fake_file_path}")
    print("\n⏳ Processing...\n")

    # 3. כאן הקסם קורה! אנחנו קוראים רק לפונקציה אחת מצינור העיבוד
    final_result = process_chat_input(user_text=user_typed_message, file_path=fake_file_path)
    
    # 4. נדפיס את התוצאה הסופית שהמערכת תחזיר למשתמש ול-AI
    print("=== 🛡️ Firewall Output ===")
    print(json.dumps(final_result, indent=2, ensure_ascii=False))
    
    # נמחק את הקובץ הזמני בסיום
    if os.path.exists(fake_file_path):
        os.remove(fake_file_path)

if __name__ == "__main__":
    test_full_pipeline()