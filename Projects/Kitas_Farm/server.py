# C:\KITA FARM\Projects\Kitas_Farm\server.py
"""
KITA FARM Coordination Server (FastAPI)
Bridges communication between:
1. Employee uploads (Telegram/Web client simulated or direct files).
2. Content creation loop (Jeejee's script and reels rendering).
3. Backoffice tracking (Korn's crop cycles).
4. An Agent Chat Coordination room so Jeejee and Korn can chat.
"""

import os
import json
import time
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="KITA FARM Integration Hub")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants & Paths
WORKSPACE_ROOT = "C:\\KITA FARM"
MEDIA_DIR = os.path.join(WORKSPACE_ROOT, "Raw", "KitaFarm_Media", "uploads")
CHATS_FILE = os.path.join(WORKSPACE_ROOT, "Projects", "Kitas_Farm", "agent_chats.json")
CROP_YIELD_FILE = os.path.join(WORKSPACE_ROOT, "Projects", "Kitas_Farm", "crop_yields.json")

os.makedirs(MEDIA_DIR, exist_ok=True)

class ChatMessage(BaseModel):
    sender: str
    message: str

# Seed sample data for chat if not exists
if not os.path.exists(CHATS_FILE):
    initial_chats = [
        {
            "timestamp": time.time() - 3600,
            "sender": "พี่กร",
            "message": "จีจี้ครับ สต็อกเรดโอ๊คสัปดาห์นี้เก็บได้สูงกว่าเป้า 15% นะครับ ฝากทำคอนเทนต์ดันยอดขายเรดโอ๊คสลัดกล่องหน่อยครับ"
        },
        {
            "timestamp": time.time() - 1800,
            "sender": "จีจี้",
            "message": "รับทราบค่ะพี่กร! เดี๋ยวจีจี้จัด Reels โปรโมตความสดของเรดโอ๊คสีม่วงสวยๆ ให้เย็นนี้เลยค่ะ คนดูเห็นแล้วต้องหิวแน่นอน!"
        }
    ]
    with open(CHATS_FILE, "w", encoding="utf-8") as f:
        json.dump(initial_chats, f, ensure_ascii=False, indent=2)

@app.get("/api/chats")
def get_chats():
    if os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@app.post("/api/chats")
def post_chat(msg: ChatMessage):
    chats = []
    if os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, "r", encoding="utf-8") as f:
            chats = json.load(f)
            
    new_chat = {
        "timestamp": time.time(),
        "sender": msg.sender,
        "message": msg.message
    }
    chats.append(new_chat)
    with open(CHATS_FILE, "w", encoding="utf-8") as f:
        json.dump(chats, f, ensure_ascii=False, indent=2)
    return new_chat

@app.get("/api/content/today")
def get_today_content():
    meta_path = os.path.join(WORKSPACE_ROOT, "Projects", "Kitas_Farm", "today_content.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"message": "ไม่มีคอนเทนต์สำหรับวันนี้ กรุณากดปุ่มสร้างด้านล่าง"}

@app.post("/api/content/generate")
def generate_content():
    import subprocess
    python_exe = "C:\\Antigravity\\GEGE\\miniconda\\python.exe"
    script_path = os.path.join(WORKSPACE_ROOT, "Projects", "Kitas_Farm", "content_planner.py")
    try:
        subprocess.run([python_exe, script_path], check=True, cwd=WORKSPACE_ROOT)
        return get_today_content()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/content/approve")
def approve_content():
    meta_path = os.path.join(WORKSPACE_ROOT, "Projects", "Kitas_Farm", "today_content.json")
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลสคริปต์ประจำวัน")
        
    with open(meta_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    data["approved"] = True
    
    # Generate the Thai gTTS audio track here during approval
    from gtts import gTTS
    audio_dir = os.path.join(WORKSPACE_ROOT, "Raw", "Voice")
    os.makedirs(audio_dir, exist_ok=True)
    audio_path = os.path.join(audio_dir, "daily_voice.mp3")
    
    try:
        script_text = data.get("script", "")
        clean_text = script_text.replace("\n", " ").replace("*", "").replace("-", "")
        tts = gTTS(text=clean_text, lang='th')
        tts.save(audio_path)
        data["voice_path"] = audio_path
    except Exception as e:
        print(f"Failed to generate gTTS: {e}")
    
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    return {"status": "approved", "data": data}

@app.post("/api/upload")
def upload_media(file: UploadFile = File(...), sender: str = Form("กิ๊ก (พนักงานฟาร์ม)")):
    # Check if the uploaded file is an audio file (Kik's voiceover recording)
    is_audio = file.filename.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg'))
    
    if is_audio:
        voice_dir = os.path.join(WORKSPACE_ROOT, "Raw", "Voice")
        os.makedirs(voice_dir, exist_ok=True)
        file_path = os.path.join(voice_dir, "daily_voice.mp3") # Keep a constant name for the video builder
    else:
        file_path = os.path.join(MEDIA_DIR, file.filename)
        
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Log upload event in agent chat
        if is_audio:
            post_chat(ChatMessage(
                sender=sender,
                message=f"🎙️ อัปโหลดไฟล์เสียงพากย์จริงสำเร็จ: {file.filename} (ระบบนำไปประกบเป็นเสียงวิดีโอแล้วค่ะ)"
            ))
        else:
            post_chat(ChatMessage(
                sender=sender,
                message=f"📤 อัปโหลดรูปภาพแปลงผักใหม่สำเร็จ: {file.filename} (สามารถนำไปประกอบคลิปได้เลยค่ะ)"
            ))
        
        return {"filename": file.filename, "status": "success", "sender": sender, "is_audio": is_audio}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/render")
def trigger_render():
    import subprocess
    python_exe = "C:\\Antigravity\\GEGE\\miniconda\\python.exe"
    script_path = os.path.join(WORKSPACE_ROOT, "Projects", "Kitas_Farm", "video_builder.py")
    try:
        # Render fast sample or today's reels
        subprocess.run([python_exe, script_path], check=True, cwd=WORKSPACE_ROOT)
        return {"status": "success", "message": "เรนเดอร์วิดีโอ Reels สำเร็จแล้ว!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import FileResponse

@app.get("/api/download/reels")
def download_reels():
    path = os.path.join(WORKSPACE_ROOT, "Projects", "Kitas_Farm", "preview_reels.mp4")
    if os.path.exists(path):
        return FileResponse(path, media_type="video/mp4", filename="daily_reels.mp4")
    raise HTTPException(status_code=404, detail="ยังไม่มีไฟล์วิดีโอที่เรนเดอร์สำเร็จ")
