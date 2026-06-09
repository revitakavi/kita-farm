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
import urllib.request
import urllib.parse
import random
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
FEEDBACK_FILE = os.path.join(WORKSPACE_ROOT, "Projects", "Kitas_Farm", "kik_feedbacks.json")
FEEDBACK_ANALYSIS_FILE = os.path.join(WORKSPACE_ROOT, "Projects", "Kitas_Farm", "hermes_feedback_analysis.md")

os.makedirs(MEDIA_DIR, exist_ok=True)

# Mount frontend files (HTML, CSS, JS) at root path
app.mount("/static", StaticFiles(directory=WORKSPACE_ROOT), name="static")

@app.get("/", response_class=HTMLResponse)
def read_root():
    index_path = os.path.join(WORKSPACE_ROOT, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Dynamic path replacement so it links style.css and app.js through the static mount
            content = content.replace('href="style.css"', 'href="/static/style.css"')
            content = content.replace('src="app.js"', 'src="/static/app.js"')
            return HTMLResponse(content=content, status_code=200)
    return HTMLResponse(content="<h1>KITA FARM Dashboard Static Index.html not found!</h1>", status_code=404)

class ChatMessage(BaseModel):
    sender: str
    message: str

class FeedbackModel(BaseModel):
    sender: str
    feedback_text: str

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
    
    # Delete old daily_voice.mp3 if it exists so we start fresh for today's new content
    old_voice = os.path.join(WORKSPACE_ROOT, "Raw", "Voice", "daily_voice.mp3")
    if os.path.exists(old_voice):
        try:
            os.remove(old_voice)
            print("Cleaned up old voice file during content generation.")
        except Exception as e:
            print(f"Failed to delete old voiceover: {e}")
            
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
    
    # We do not generate gTTS AI voiceover anymore, as Kik will record it manually.
    data["voice_path"] = ""
    
    # Delete old daily_voice.mp3 if it exists so we start fresh for today
    old_voice = os.path.join(WORKSPACE_ROOT, "Raw", "Voice", "daily_voice.mp3")
    if os.path.exists(old_voice):
        try:
            os.remove(old_voice)
        except Exception as e:
            print(f"Failed to delete old voiceover: {e}")
    
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

@app.post("/api/content/generate-visuals")
def generate_ai_visuals():
    meta_path = os.path.join(WORKSPACE_ROOT, "Projects", "Kitas_Farm", "today_content.json")
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลสคริปต์ประจำวัน กรุณาสร้างสคริปต์ก่อนค่ะ")
        
    with open(meta_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Set visual mode to ai_generated
    data["visual_mode"] = "ai_generated"
    
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    ai_dir = os.path.join(WORKSPACE_ROOT, "Raw", "KitaFarm_Media", "ai_generated")
    os.makedirs(ai_dir, exist_ok=True)
    
    scenes = data.get("shooting_scenes", [])
    topic = data.get("topic", "Hydroponics salad greens")
    
    # Clear old generated visuals
    for f_name in os.listdir(ai_dir):
        if f_name.endswith(".jpg"):
            try:
                os.remove(os.path.join(ai_dir, f_name))
            except:
                pass

    # Load local facebook tags db if it exists
    tags_file = os.path.join(WORKSPACE_ROOT, "Projects", "Kitas_Farm", "facebook_image_tags.json")
    fb_dir = os.path.join(WORKSPACE_ROOT, "Raw", "KitaFarm_Media", "facebook", "KITA FARM - คีตะฟาร์ม", "KITA FARM - คีตะฟาร์ม's photos (pb.100067117794424.-2207520000)")
    
    tags_db = {}
    if os.path.exists(tags_file):
        try:
            with open(tags_file, "r", encoding="utf-8") as f:
                tags_db = json.load(f)
        except Exception as e:
            print(f"Error reading local tags database: {e}")

    downloaded = 0
    for idx, scene in enumerate(scenes[:3]):
        desc = scene.get("description", "")
        desc_lower = desc.lower()
        topic_lower = topic.lower()
        
        # 1. Determine keywords based on the scene and topic to search the local database
        keywords = ["salad", "lettuce", "hydroponics"]
        if "red" in topic_lower or "เรด" in topic_lower:
            keywords.append("red oak")
            keywords.append("red")
        elif "butter" in topic_lower or "บัตเตอร์" in topic_lower:
            keywords.append("butterhead")
        elif "cos" in topic_lower or "คอส" in topic_lower:
            keywords.append("cos")
        elif "finlay" in topic_lower or "ฟินเล่" in topic_lower or "frillice" in topic_lower:
            keywords.append("frillice")

        if "greenhouse" in desc_lower or "โรงเรือน" in desc_lower:
            keywords.append("greenhouse")
            keywords.append("farm")
        if "harvest" in desc_lower or "เก็บ" in desc_lower or "เด็ด" in desc_lower:
            keywords.append("harvest")
            keywords.append("farming activity")
            keywords.append("packing")
        
        target_path = os.path.join(ai_dir, f"scene_{idx+1}.jpg")
        
        # 2. Try to find a matching photo in local database first
        matched_photo = None
        if tags_db and os.path.exists(fb_dir):
            matches = []
            for filename, tags in tags_db.items():
                score = 0
                for kw in keywords:
                    for tag in tags:
                        if kw in tag.lower() or tag.lower() in kw:
                            score += 1
                if score > 0:
                    full_p = os.path.join(fb_dir, filename)
                    if os.path.exists(full_p):
                        matches.append((score, full_p))
            if matches:
                # Sort by score descending
                matches.sort(key=lambda x: x[0], reverse=True)
                top_score = matches[0][0]
                top_matches = [m[1] for m in matches if m[0] == top_score]
                matched_photo = random.choice(top_matches)
                
        if matched_photo:
            try:
                shutil.copy(matched_photo, target_path)
                downloaded += 1
                print(f"Matched Scene {idx+1} to local image: {matched_photo} (Keywords: {keywords})")
                continue
            except Exception as e:
                print(f"Failed to copy local matched image: {e}")

        # 3. Fallback to LoremFlickr using a SINGLE keyword based on the scene context
        # This prevents getting default cat/meme images from LoremFlickr when multiple tags fail
        flickr_tag = "lettuce"
        if "greenhouse" in keywords:
            flickr_tag = "greenhouse"
        elif "harvest" in keywords:
            flickr_tag = "farming"
        elif "red oak" in keywords:
            flickr_tag = "red-lettuce"
        elif "butterhead" in keywords:
            flickr_tag = "lettuce"
        elif "cos" in keywords:
            flickr_tag = "lettuce"
            
        flickr_url = f"https://loremflickr.com/1080/1920/{flickr_tag}?lock={idx+1}"
        print(f"Fallback to LoremFlickr for Scene {idx+1} using tag '{flickr_tag}': {flickr_url}")
        
        try:
            req = urllib.request.Request(
                flickr_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=15) as response, open(target_path, "wb") as out_file:
                out_file.write(response.read())
                
            if os.path.exists(target_path) and os.path.getsize(target_path) > 1000:
                # Ensure it's not the default cat placeholder (size 234114 bytes)
                if os.path.getsize(target_path) == 234114:
                    print(f"LoremFlickr returned the default cat image for Scene {idx+1}. Removing.")
                    os.remove(target_path)
                else:
                    downloaded += 1
                    print(f"Successfully downloaded LoremFlickr scene_{idx+1}.jpg, size: {os.path.getsize(target_path)}")
        except Exception as e:
            print(f"LoremFlickr fallback failed: {e}")
            if os.path.exists(target_path):
                try: os.remove(target_path)
                except: pass

        # 4. Ultimate fallback: Pick a random image from the facebook pool (even if no tags matched)
        if not os.path.exists(target_path) or os.path.getsize(target_path) < 1000:
            print(f"Final fallback: Copying random image from facebook pool for Scene {idx+1}")
            if os.path.exists(fb_dir):
                import glob
                fb_images = glob.glob(os.path.join(fb_dir, "*.jpg"))
                if fb_images:
                    src = random.choice(fb_images)
                    try:
                        shutil.copy(src, target_path)
                        downloaded += 1
                        print(f"Copied random fallback image: {src}")
                    except Exception as e:
                        print(f"Failed to copy final fallback: {e}")
        
        time.sleep(0.5)

    # Now render the video automatically
    import subprocess
    python_exe = "C:\\Antigravity\\GEGE\\miniconda\\python.exe"
    script_path = os.path.join(WORKSPACE_ROOT, "Projects", "Kitas_Farm", "video_builder.py")
    try:
        subprocess.run([python_exe, script_path], check=True, cwd=WORKSPACE_ROOT)
        
        # Log to chat
        post_chat(ChatMessage(
            sender="คุณกี้",
            message=f"🤖 สื่อสตอรี่บอร์ดจัดทำเสร็จแล้วค่ะ! เลือกภาพจากระบบ {downloaded} ซีน และทำการเรนเดอร์วิดีโอเรียบร้อยแล้วค่ะ สามารถตรวจสอบวิดีโอ Reels ได้ทันทีนะคะ!"
        ))
        
        return {"status": "success", "message": f"เตรียมภาพประกอบวิดีโอสำเร็จ {downloaded} ภาพ และเรนเดอร์วิดีโอเรียบร้อยแล้วค่ะ"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ประกอบคลิปไม่สำเร็จหลังจัดเตรียมภาพ: {str(e)}")

@app.post("/api/feedback")
def post_feedback(fb: FeedbackModel):
    feedbacks = []
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
                feedbacks = json.load(f)
        except:
            pass
    feedbacks.append({
        "timestamp": time.time(),
        "sender": fb.sender,
        "feedback_text": fb.feedback_text
    })
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(feedbacks, f, ensure_ascii=False, indent=2)
        
    post_chat(ChatMessage(
        sender=fb.sender,
        message=f"📝 ส่งข้อเสนอแนะหน้างาน: \"{fb.feedback_text[:60]}...\" เข้าสู่ระบบหลังบ้านสำเร็จแล้วค่ะ!"
    ))
    return {"status": "success", "message": "บันทึกข้อเสนอแนะเรียบร้อยแล้วค่ะ"}

@app.post("/api/feedback/analyze")
def analyze_feedbacks():
    if not os.path.exists(FEEDBACK_FILE):
        return {"analysis": "ยังไม่มีรายงานข้อเสนอแนะจากน้องกิ๊กส่งเข้ามาในระบบค่ะ"}
        
    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        feedbacks = json.load(f)
        
    if not feedbacks:
        return {"analysis": "ยังไม่มีรายงานข้อเสนอแนะจากน้องกิ๊กส่งเข้ามาในระบบค่ะ"}
        
    # Format feedback texts for LLM
    formatted_feedbacks = ""
    for idx, fb in enumerate(feedbacks):
        t_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(fb['timestamp']))
        formatted_feedbacks += f"[{t_str}] จาก {fb['sender']}: {fb['feedback_text']}\n---\n"
        
    prompt = (
        "You are 'Hermes', the backend AI assistant auditor for KITA FARM. "
        "Analyze these operational feedbacks submitted by the field workers and write a detailed audit summary report in Thai. "
        "Highlight: \n"
        "1) App/Technical issues (e.g. video rendering, RAG quality, UI lag)\n"
        "2) Greenhouse / Hydroponics issues (e.g. water EC level, seeding survival rate, temperature problems)\n"
        "3) Actionable priorities for Kee to solve the problems.\n\n"
        "Write in natural and professional Thai. Do not include thinking tags."
    )
    
    ollama_url = "http://localhost:11434/api/generate"
    data = {
        "model": "nous-hermes",
        "prompt": f"{prompt}\n\nFeedbacks list:\n{formatted_feedbacks}",
        "stream": False
    }
    try:
        import urllib.request
        req = urllib.request.Request(
            ollama_url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as response:
            res = json.loads(response.read().decode("utf-8"))
            analysis = res.get("response", "").strip()
            
            with open(FEEDBACK_ANALYSIS_FILE, "w", encoding="utf-8") as f_out:
                f_out.write(analysis)
                
            post_chat(ChatMessage(
                sender="Hermes",
                message="🔍 วิเคราะห์ฟีดแบ็กจากหน้างานเสร็จเรียบร้อยแล้วครับพี่กี้! สรุปข้อมูลใส่แดชบอร์ดให้แล้วครับ"
            ))
            return {"analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama (nous-hermes) Analysis failed: {e}")

@app.get("/api/feedback/analysis")
def get_feedback_analysis():
    if os.path.exists(FEEDBACK_ANALYSIS_FILE):
        with open(FEEDBACK_ANALYSIS_FILE, "r", encoding="utf-8") as f:
            return {"analysis": f.read()}
    return {"analysis": "ยังไม่มีรายงานวิเคราะห์ฟีดแบ็กจาก Hermes กดปุ่มวิเคราะห์เพื่ออัปเดตรายงานล่าสุดค่ะ"}

from fastapi.responses import FileResponse

@app.get("/api/download/reels")
def download_reels():
    path = os.path.join(WORKSPACE_ROOT, "Projects", "Kitas_Farm", "preview_reels.mp4")
    if os.path.exists(path):
        return FileResponse(path, media_type="video/mp4", filename="daily_reels.mp4")
    raise HTTPException(status_code=404, detail="ยังไม่มีไฟล์วิดีโอที่เรนเดอร์สำเร็จ")
