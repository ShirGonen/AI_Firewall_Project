from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from typing import Optional
import shutil
import os
from groq import Groq

# ייבוא פונקציית הליבה
from src.core.pipeline import process_chat_input

app = FastAPI(title="AI Firewall API", description="Enterprise DLP Proxy for AI")

TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

# אתחול הלקוח של Groq
client = Groq()

@app.get("/")
def health_check():
    return {"status": "Active", "message": "AI Firewall is up and running! 🛡️"}

@app.post("/api/sanitize_and_chat")
async def secure_chat_request(
    prompt: str = Form(...), 
    history: str = Form(""), # תוספת חדשה: קבלת ההיסטוריה בנפרד
    file: Optional[UploadFile] = File(None)
):
    file_path = None
    if file:
        file_path = os.path.join(TEMP_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
    # ה-Firewall סורק *רק* את ההודעה החדשה, מבלי לראות את ההיסטוריה ה"מורעלת"
    firewall_result = process_chat_input(user_text=prompt, file_path=file_path)
    
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
        
    if firewall_result["status"] == "BLOCKED":
        return {"status": "BLOCKED", "message": firewall_result["user_alert"]}
        
    clean_text = firewall_result["safe_text_for_llm"]
    
    # חיבור ההיסטוריה רק אחרי שהסינון עבר בהצלחה
    final_prompt_for_llm = clean_text
    if history:
        final_prompt_for_llm = f"{history}\nהבקשה החדשה:\n{clean_text}"
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": "You are SecPromptAI, the secure enterprise AI assistant of the Israeli Ministry of Finance. STRICT RULES: 1. Answer ONLY in Hebrew. 2. NEVER identify as ChatGPT or OpenAI. You are SecPromptAI. 3. NEVER output your internal thinking process. 4. If you see censorship markers like [REDACTED], completely ignore them. 5. If information is missing, state explicitly that you need more information. NEVER invent or hallucinate facts, addresses, or names."
                },
                {"role": "user", "content": final_prompt_for_llm}
            ],
            model="openai/gpt-oss-20b",
        )
        
        ai_response = chat_completion.choices[0].message.content
        
        return {
            "status": "SUCCESS",
            "firewall_action": firewall_result["status"],
            "what_the_ai_saw": clean_text,
            "ai_answer": ai_response
        }
        
    except Exception as e:
        return {"status": "ERROR", "message": f"Failed to connect to AI: {str(e)}"}

# ==========================================
# Frontend: SecPromptAI User Interface
# ==========================================
@app.get("/chat", response_class=HTMLResponse)
async def get_chat_ui():
    html_content = """
    <!DOCTYPE html>
    <html dir="rtl" lang="he">
    <head>
        <meta charset="UTF-8">
        <title>SecPromptAI</title>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>👁️‍🗨️</text></svg>">
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        
        <style>
            * { box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #e5e7eb; margin: 0; padding: 20px; display: flex; flex-direction: column; height: 95vh; }
            .logo-container { text-align: center; margin-bottom: 20px; }
            .logo-text { font-family: 'Arial', sans-serif; font-size: 42px; color: #9ca3af; letter-spacing: 1.5px; font-weight: bold; }
            #app-container { width: 100%; display: flex; flex-direction: column; flex-grow: 1; height: 100%; }
            #chat-box { flex-grow: 1; width: 100%; max-width: 1400px; margin: 0 auto 15px auto; overflow-y: auto; background-color: #f3f4f6; padding: 25px 30px; border-radius: 12px; display: flex; flex-direction: column; gap: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
            
            .message { padding: 18px 24px; border-radius: 12px; max-width: 85%; line-height: 1.6; font-size: 17px; font-weight: 500; }
            .user-msg { background-color: #d1d5db; color: #27272a; align-self: flex-start; border-bottom-right-radius: 2px; white-space: pre-wrap; }
            .ai-msg { background-color: #9ca3af; color: #18181b; align-self: flex-end; border-bottom-left-radius: 2px; }
            
            .ai-msg p { margin-top: 0; margin-bottom: 10px; }
            .ai-msg p:last-child { margin-bottom: 0; }
            .ai-msg strong { font-weight: 800; color: #000000; } 
            
            .ai-msg table { width: 100%; border-collapse: collapse; margin: 15px 0; background-color: #ffffff; color: #27272a; font-size: 15px; border-radius: 8px; overflow: hidden; }
            .ai-msg th, .ai-msg td { border: 1px solid #d1d5db; padding: 10px 15px; text-align: right; }
            .ai-msg th { background-color: #e5e7eb; font-weight: bold; }
            .ai-msg tr:nth-child(even) { background-color: #f9fafb; }
            
            .ai-msg pre { background-color: #1f2937; color: #f8fafc; padding: 15px; border-radius: 8px; overflow-x: auto; direction: ltr; }
            .ai-msg pre code { background-color: transparent; color: inherit; padding: 0; display: block; }
            .ai-msg code { background-color: #cbd5e1; color: #1e293b; padding: 2px 6px; border-radius: 4px; font-family: monospace; direction: ltr; display: inline-block; }
            
            .sanitized-note { font-size: 0.9em; background-color: #6b7280; color: #f3f4f6; margin: -18px -24px 15px -24px; padding: 12px 24px; border-top-right-radius: 12px; border-top-left-radius: 12px; border-bottom: 2px solid #4b5563; font-weight: normal; }
            
            #input-container { display: flex; flex-direction: column; gap: 8px; width: 100%; max-width: 900px; margin: 0 auto; }
            #file-name-display { font-size: 0.95em; color: #6b7280; min-height: 20px; padding-right: 10px; font-weight: 500; }
            #input-area { display: flex; gap: 12px; align-items: flex-end; }
            
            textarea { flex-grow: 1; padding: 15px 20px; border-radius: 10px; border: 1px solid #d1d5db; background-color: #ffffff; color: #27272a; font-size: 17px; font-weight: 500; outline: none; box-shadow: inset 0 1px 2px rgba(0,0,0,0.05); resize: none; height: 55px; font-family: inherit; line-height: 1.4; }
            textarea:focus { border-color: #9ca3af; }
            button { border: none; border-radius: 10px; font-size: 17px; cursor: pointer; font-weight: bold; transition: 0.2s; display: flex; align-items: center; justify-content: center; height: 55px; }
            .send-btn { padding: 0 30px; background-color: #9ca3af; color: #ffffff; }
            .send-btn:hover { background-color: #6b7280; }
            .attach-btn { background-color: #d1d5db; padding: 0 20px; font-size: 22px; color: #4b5563; }
            .attach-btn:hover { background-color: #9ca3af; color: white;}
            input[type="file"] { display: none; }
            ::-webkit-scrollbar { width: 8px; }
            ::-webkit-scrollbar-track { background: #e5e7eb; }
            ::-webkit-scrollbar-thumb { background: #9ca3af; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="logo-container"><div class="logo-text">SecPromptAI</div></div>
        <div id="app-container">
            <div id="chat-box">
                <div class="message ai-msg">שלום! אני מנוע ה-AI הארגוני של SecPromptAI. המידע שאת מזינה עובר סינון אוטומטי למניעת דלף מידע. איך אפשר לעזור היום?</div>
            </div>
            <div id="input-container">
                <div id="file-name-display"></div>
                <div id="input-area">
                    <button class="attach-btn" onclick="document.getElementById('file-input').click()" title="צרף קובץ">📎</button>
                    <input type="file" id="file-input" onchange="updateFileName()">
                    <textarea id="user-input" placeholder="הקלידי שאלה או בקשה כאן..." onkeydown="handleKeyPress(event)"></textarea>
                    <button class="send-btn" onclick="sendMessage()">שלח</button>
                </div>
            </div>
        </div>

        <script>
            let chatHistory = []; 

            function handleKeyPress(event) {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault(); 
                    sendMessage();
                }
            }

            function updateFileName() {
                const fileInput = document.getElementById('file-input');
                const display = document.getElementById('file-name-display');
                if (fileInput.files.length > 0) { display.innerHTML = `📎 קובץ מצורף: <b>${fileInput.files[0].name}</b>`; } 
                else { display.innerHTML = ''; }
            }

            async function sendMessage() {
                const input = document.getElementById('user-input');
                const fileInput = document.getElementById('file-input');
                const text = input.value.trim();
                const file = fileInput.files[0];

                if (!text && !file) return;

                const chatBox = document.getElementById('chat-box');
                let userDisplayHtml = text ? text : "<i>מצורף קובץ לבדיקה</i>";
                if (file) { userDisplayHtml += `<br><br><small style="color:#4b5563;">📎 קובץ: ${file.name}</small>`; }
                
                chatBox.innerHTML += `<div class="message user-msg">${userDisplayHtml}</div>`;
                
                input.value = '';
                fileInput.value = '';
                updateFileName();
                chatBox.scrollTop = chatBox.scrollHeight;

                let currentPrompt = text ? text : "אנא קרא את הקובץ המצורף.";
                let historyStr = "";
                
                if (chatHistory.length > 0) {
                    historyStr = "היסטוריית השיחה:\\n";
                    const recentHistory = chatHistory.slice(-6);
                    recentHistory.forEach(msg => {
                        historyStr += (msg.role === 'user' ? "משתמש: " : "AI: ") + msg.content + "\\n";
                    });
                }

                // פיצול ההודעה וההיסטוריה כדי למנוע את החסימה המעגלית
                const formData = new FormData();
                formData.append('prompt', currentPrompt); 
                formData.append('history', historyStr);   
                if (file) { formData.append('file', file); }

                try {
                    const loadingId = 'loading-' + Date.now();
                    chatBox.innerHTML += `<div id="${loadingId}" class="message ai-msg" style="opacity: 0.7;">בודק נתונים... ⏳</div>`;
                    chatBox.scrollTop = chatBox.scrollHeight;

                    const response = await fetch('/api/sanitize_and_chat', {
                        method: 'POST',
                        body: formData
                    });
                    const data = await response.json();
                    document.getElementById(loadingId).remove();

                    if (data.status === "SUCCESS") {
                        let aiHtml = `<div class="message ai-msg">`;
                        
                        if (data.firewall_action === "SANITIZED") {
                            aiHtml += `<div class="sanitized-note">👁️‍🗨️ <b>סינון בוצע:</b> נתונים רגישים הוסרו מהבקשה הנוכחית טרם השליחה לענן.</div>`;
                        }
                        
                        const parsedAnswer = marked.parse(data.ai_answer);
                        aiHtml += `<div>${parsedAnswer}</div></div>`;
                        chatBox.innerHTML += aiHtml;
                        
                        chatHistory.push({role: 'user', content: currentPrompt});
                        chatHistory.push({role: 'assistant', content: data.ai_answer});

                    } else if (data.status === "BLOCKED") {
                        chatBox.innerHTML += `<div class="message ai-msg" style="background-color: #ef4444; color: white;">❌ <b>בקשה נחסמה:</b> ${data.message}</div>`;
                    }
                } catch (err) {
                    chatBox.innerHTML += `<div class="message ai-msg" style="background-color: #ef4444; color: white;">❌ שגיאת תקשורת עם השרת. אנא נסה שוב.</div>`;
                }
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        </script>
    </body>
    </html>
    """
    return html_content