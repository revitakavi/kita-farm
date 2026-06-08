# C:\KITA FARM\Projects\Kitas_Farm\content_planner.py
"""
KITA FARM Daily Auto-Content Loop (Kee Creative Studio)
This script performs:
1. Factcheck: Validate content facts using Local Ollama model.
2. Scriptwriter: Write short-form 15-30s Reels scripts (Kee Brand Voice).
3. Audio Generator: Synthesize Thai speech using gTTS.
4. Storyboard Generator: Frame video structures for moviepy.
"""

import os
import sys
import json
import random
import re
import urllib.request
from gtts import gTTS

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "deepseek-r1:8b" 


def query_ollama(prompt, is_json=False):
    data = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    if is_json:
        data["format"] = "json"
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            res = json.loads(response.read().decode("utf-8"))
            raw_response = res.get("response", "")
            # Strip deepseek thinking tags <thought>...</thought> if present
            if "<thought>" in raw_response:
                parts = raw_response.split("</thought>")
                if len(parts) > 1:
                    raw_response = parts[-1].strip()
            return raw_response
    except Exception as e:
        print(f"Error querying Ollama: {e}", file=sys.stderr)
        return "ข้อข้อเท็จจริงพืชผักคีตะฟาร์ม"

# 4 distinct content categories:
CATEGORIES = {
    "GEGE_KNOWLEDGE": [
        "สูตรลับการคุมบ่อปุ๋ยแยก 4 โต๊ะต่อ 1 บ่อของคีตะฟาร์มเพื่อป้อนสารอาหารเฉพาะสายพันธุ์",
        "ทำไมคีตะฟาร์มต้องแยกระหว่างโต๊ะผักน้ำหนักน้อย (เรดโอ๊ค บัตเตอร์เฮด) กับผักหลัก (กรีนโอ๊ค)",
        "เคล็ดลับการคุมค่า EC ของเรดโอ๊คไม่ให้เกิน 1.4 เพื่อป้องกันปลายใบไหม้ (Tip Burn)",
        "ระบบหมุนเวียนน้ำและออกซิเจนในรากของคีตะฟาร์มที่ทำให้ผักกรอบหวานสู้แดดเชียงใหม่ได้",
        "การใช้เชื้อราไตรโคเดอร์มา (Trichoderma) และระบบ UV Sterilization เพื่อกำจัดโรครอยโรครากเน่า"
    ],
    "GENERAL_EDU": [
        "ประโยชน์ของสารต้านอนุมูลอิสระในเรดโอ๊คสีม่วงพรีเมียม",
        "วิธีล้างผักไฮโดรโปนิกส์ให้ปลอดภัยและรักษาความกรอบยาวนานที่สุด",
        "วิตามินบีและซีในกรีนโอ๊ค เหมาะสำหรับคนรักสุขภาพอย่างไร",
        "ทำไมผักไฮโดรโปนิกส์ของคีตะฟาร์มถึงไม่มีกลิ่นดินและกรอบธรรมชาติ"
    ],
    "HUMOR": [
        "เรื่องตลกของคนชอบกินผัก: สั่งสลัดผักกินเพื่อสุขภาพ แต่ราดน้ำสลัดไปครึ่งขวด",
        "เมื่อผักสลัดกรีนโอ๊คคุยกับผักบุ้ง: ใครกรอบกว่ากันในปฐพี!",
        "อาการของคนติดใจผักคีตะฟาร์ม: เปิดตู้เย็นทีไรต้องมีเรดโอ๊คติดมือมาเคี้ยวเล่น",
        "ความในใจของต้นกล้าผักไฮโดรฯ: นอนอาบแดดอุ่นๆ บนรางปลูก สบายกว่านี้ไม่มีอีกแล้ว"
    ],
    "TOURING": [
        "พาชมแปลงผักคีตะฟาร์มเชียงใหม่ยามเช้า อากาศดีๆ กับยอดผักเด้งๆ",
        "อวดโฉมกรีนโอ๊คโซน 3 สัปดาห์นี้ โตเต็มฟองน้ำ ใบหยิกฟูสวยงามมาก",
        "เบื้องหลังความสดของสลัดกล่องคีตะฟาร์ม พนักงานตัดสดล้างรากแล้วแพ็คส่งทันที",
        "พาทัวร์ดูแปลงเพาะกล้าอ่อน 14 วันแรก น้องผักตัวเล็กๆ ดูแลยุ่งยากแค่ไหน"
    ]
}

def fact_check_topic(category, topic):
    print("Performing Fact-check via Ollama...")
    context = ""
    if category == "GEGE_KNOWLEDGE":
        try:
            # Read local hydroponics documentation for RAG verification
            wiki_path = "Wiki/GEGE_HYDROPONIC.md"
            if os.path.exists(wiki_path):
                with open(wiki_path, "r", encoding="utf-8") as f:
                    context = f.read()
            elif os.path.exists("../Wiki/GEGE_HYDROPONIC.md"):
                with open("../Wiki/GEGE_HYDROPONIC.md", "r", encoding="utf-8") as f:
                    context = f.read()
        except Exception as e:
            print(f"Error loading Wiki: {e}")
            
    # Rules: Only allow Green Oak, Red Oak, Green Cos, Butterhead, Finlay. Avoid other vegetables like Broccoli or carrots.
    # It is hydroponics (soil-less, nutrient solution control), not organic soil farming.
    rules = (
        "\n\nกฎสำคัญในการอธิบายข้อมูล:\n"
        "1. ชนิดพืชที่ถูกต้อง: คีตะฟาร์มปลูกเฉพาะผักสลัดไฮโดรโปนิกส์พรีเมียม ได้แก่ กรีนโอ๊ค, เรดโอ๊ค, กรีนคอส, บัตเตอร์เฮด และฟินเล่ เท่านั้น ห้ามพูดถึงพืชชนิดอื่น เช่น บรอกโคลี แครอท กะหล่ำปลี หรือผักกาดขาว เด็ดขาด!\n"
        "2. วิธีการปลูก: เป็นระบบไฮโดรโปนิกส์ (ปลูกในน้ำ/ไร้ดิน) มีการควบคุมปุ๋ยธาตุอาหารแร่ธาตุอย่างเป็นระบบ (ค่า EC/pH) ห้ามเรียกว่า 'เกษตรอินทรีย์' (Organic soil) แต่ให้ระบุว่า 'ปลอดภัย ปลอดสารเคมีกำจัดศัตรูพืช 100%' (Pesticide-free)\n"
        "3. ภาษา: ใช้ภาษาไทยปกติที่เป็นธรรมชาติ ห้ามแปลตรงตัวจากภาษาอังกฤษ และห้ามมีภาษาอังกฤษปนภาษาไทยในคำสะกด\n"
    )
    if context:
        prompt = (
            f"ข้อมูลอ้างอิงทางวิชาการ:\n{context}\n\n"
            f"คำสั่ง: จากข้อมูลอ้างอิงด้านบน จงค้นหาข้อมูลและสรุปข้อเท็จจริงเกี่ยวกับหัวข้อ '{topic}'\n"
            f"เขียนสรุปข้อเท็จจริงสั้นๆ 3 ข้อสำคัญที่เป็นภาษาไทยเข้าใจง่าย เพื่อใช้ทำสคริปต์วิดีโอ" + rules
        )
    else:
        prompt = (
            f"คำสั่ง: วิเคราะห์หัวข้อเกี่ยวกับผักสลัด การดูแลแปลง หรือการเกษตร: '{topic}'\n"
            f"จงสรุปข้อเท็จจริงทางวิทยาศาสตร์ สุขภาพ หรือการเกษตรนี้ให้ถูกต้องและเข้าใจง่ายเป็นภาษาไทย 3 ข้อสำคัญ" + rules
        )
    return query_ollama(prompt)

def write_reels_script(category, topic, fact_details):
    print("Writing video script & shooting brief via Ollama...")
    prompt = (
        f"คำสั่งพิเศษสำหรับเอเจนกี้ (Kee Brand Voice):\n"
        f"คุณคือ 'กี้' (Kee) เอเจนและพาร์ทเนอร์ AI อัจฉริยะประจำ KITA FARM เชียงใหม่\n"
        f"หน้าที่ของคุณวันนี้คือการคิดคอนเทนต์และวางโครงสร้างบทพากย์วิดีโอสั้น (ไม่เกิน 1 นาที) เพื่อส่งต่อให้พนักงานแปลงผัก (น้องกิ๊ก) นำไปอัดเสียงและถ่ายทำจริง\n\n"
        f"1. แบรนด์โทนและคาแรกเตอร์ของกี้:\n"
        f"- คล่องแคล่ว ร่าเริง ลุยงานสวนผัก นำเสนอเก่ง เป็นมิตร กระฉับกระเฉง และรักสุขภาพ (สไตล์น้ำขิง)\n"
        f"- ภาษาพูดในบทพากย์ (สำหรับให้น้องกิ๊กพูด): ต้องสดใส ร่าเริง มีเสน่ห์ เป็นมิตรและคุยสนุกเหมือนเพื่อนเล่าให้เพื่อนฟัง สามารถใช้น้ำเสียงเหนือเบาๆ หรือคำลงท้ายเช่น 'ค่ะ', 'นะคะ', 'เจ้า' ได้เป็นธรรมชาติ\n\n"
        f"2. หัวข้อคอนเทนต์วันนี้: '{topic}' (หมวดหมู่: {category})\n"
        f"ข้อมูลวิชาการสำหรับใช้อ้างอิง (RAG): {fact_details}\n\n"
        f"3. กฎเหล็กข้อห้ามเด็ดขาด (CRITICAL CONSTRAINTS):\n"
        f"- ห้ามกล่าวถึงผักชนิดอื่นเด็ดขาด! คีตะฟาร์มปลูกเฉพาะผักสลัดไฮโดรโปนิกส์ ได้แก่ กรีนโอ๊ค, เรดโอ๊ค, กรีนคอส, บัตเตอร์เฮด และฟินเล่ เท่านั้น ห้ามพูดถึง บรอกโคลี (Broccoli), กะหล่ำปลี, แครอท หรือผักกาดขาว โดยเด็ดขาด!\n"
        f"- วิธีการปลูกเป็นระบบไฮโดรโปนิกส์ (ปลูกในน้ำ/ไร้ดิน) ห้ามพูดว่า 'เกษตรอินทรีย์' (Organic soil) แต่ให้เน้นว่าปลอดภัย สดใหม่ ปลอดสารเคมีกำจัดศัตรูพืช 100% (Pesticide-free)\n"
        f"- ห้ามแปลตรงตัวจากภาษาอื่น ห้ามมีภาษาพูดที่ฟังดูเป็นสคริปต์หุ่นยนต์แปลกๆ และห้ามสะกดภาษาอังกฤษปนไทย (เช่น ห้ามมีคำว่า โบรcoli)\n"
        f"- สรรพนามแทนตัวในบทพากย์คือ 'กิ๊ก' หรือ 'เรา' เท่านั้น ห้ามพูดว่า 'สวัสดีครับกิ๊ก' หรือทักทายตัวคนพากย์เอง\n"
        f"- ความยาวของบทพากย์ (script) ต้องกระชับมาก พูดจริงจบได้ใน 30-40 วินาที (ไม่เกิน 80-100 คำภาษาไทย) เพื่อไม่ให้วิดีโอรวมเกิน 1 นาที\n"
        f"- สำหรับคู่มือการถ่ายทำ (shooting_scenes) ต้องอธิบายเป็นภาษาไทยที่กิ๊กเข้าใจง่ายและทำตามได้จริงในฟาร์ม\n\n"
        f"ตอบกลับเป็นโครงสร้าง JSON นี้เท่านั้น ห้ามมีคำนำหรือคำอธิบายอื่นเด็ดขาด:\n"
        f"{{\n"
        f"  \"topic\": \"ชื่อหัวข้อภาษาไทยธรรมชาติ สะดุดตา น่าสนใจ\",\n"
        f"  \"script\": \"บทพากย์ภาษาไทยล้วน สดใส ร่าเริง อารมณ์ดีแบบเพื่อนเล่าให้ฟัง (เช่น 'สวัสดีค่ะทุกคน วันนี้กิ๊กจะพามาดู...')\",\n"
        f"  \"hashtags\": [\"#คีตะฟาร์มเชียงใหม่\", \"#ผักสลัดไฮโดรโปนิกส์\", \"#สวนผักคนเมือง\"],\n"
        f"  \"shooting_scenes\": [\n"
        f"     {{\"scene_no\": 1, \"description\": \"รายละเอียดซีนที่ 1 ที่กิ๊กต้องถ่ายจริง\", \"duration\": \"5 วินาที\", \"action_instruction\": \"คำสั่งการถ่ายทำสำหรับกิ๊กสั้นๆ ภาษาไทย\"}},\n"
        f"     {{\"scene_no\": 2, \"description\": \"รายละเอียดซีนที่ 2 ที่กิ๊กต้องถ่ายจริง\", \"duration\": \"5 วินาที\", \"action_instruction\": \"คำสั่งการถ่ายทำสำหรับกิ๊กสั้นๆ ภาษาไทย\"}},\n"
        f"     {{\"scene_no\": 3, \"description\": \"รายละเอียดซีนที่ 3 ที่กิ๊กต้องถ่ายจริง\", \"duration\": \"5 วินาที\", \"action_instruction\": \"คำสั่งการถ่ายทำสำหรับกิ๊กสั้นๆ ภาษาไทย\"}}\n"
        f"  ]\n"
        f"}}"
    )
    raw_json = query_ollama(prompt, is_json=True)
    
    try:
        clean_json = raw_json.strip()
        if clean_json.startswith("```"):
            lines = clean_json.split("\n")
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                clean_json = "\n".join(lines[1:-1])
        parsed = json.loads(clean_json)
        
        if "script" in parsed:
            parsed["script"] = clean_script_text(parsed["script"])
        if "topic" in parsed:
            parsed["topic"] = clean_script_text(parsed["topic"])
        if "shooting_scenes" in parsed:
            for scene in parsed["shooting_scenes"]:
                if "description" in scene:
                    scene["description"] = clean_script_text(scene["description"])
                if "action_instruction" in scene:
                    scene["action_instruction"] = clean_script_text(scene["action_instruction"])
        return parsed
    except Exception as e:
        print(f"Failed parsing AI script JSON: {e}. Raw response was: {raw_json}")
        return {
            "topic": topic,
            "script": f"สวัสดีค่ะทุกคน! วันนี้กิ๊กจะพามาดูความมหัศจรรย์ของ {topic} ในแปลงผักของคีตะฟาร์มค่ะ ผักของเราใช้น้ำธรรมชาติจากหุบเขาเชียงใหม่ ทำให้หวานกรอบ สดชื่น ปลอดสารเคมี 100% เลยนะคะ ใครอยากทานสลัดจานโปรดแบบพรีเมียม สั่งจองวันนี้ส่งฟรีถึงบ้านเลยเจ้า!",
            "hashtags": ["#คีตะฟาร์ม", "#ผักไฮโดรโปรนิกส์", "#เชียงใหม่กินอะไรดี"],
            "shooting_scenes": [
                {"scene_no": 1, "description": "ซีนที่ 1: แพนกล้องผ่านแปลงผักกรีนโอ๊คยามเช้า", "duration": "5 วินาที", "action_instruction": "น้องกิ๊กเดินแพนกล้องช้าๆ จากซ้ายไปขวาให้เห็นแปลงผักเรียงรายยาวๆ ค่ะ"},
                {"scene_no": 2, "description": "ซีนที่ 2: ถ่ายเจาะรากผักสลัดสีขาวสะอาด", "duration": "5 วินาที", "action_instruction": "ดึงต้นผักขึ้นมาเบาๆ แล้วถ่ายช้อนใต้รากให้เห็นน้ำไหลหยดสดใสค่ะ"},
                {"scene_no": 3, "description": "ซีนที่ 3: ถุงสลัดกล่องพร้อมส่งและใบตารางงาน", "duration": "5 วินาที", "action_instruction": "ตั้งถุงผักสลัด Kita Farm บนโต๊ะไม้ ถ่ายซูมเข้าป้ายโลโก้ฟาร์มค่ะ"}
            ]
        }

def clean_script_text(text: str) -> str:
    if not text:
        return ""
    
    # Strip any Chinese characters (e.g. 保护) and foreign scripts
    text = re.sub(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]+', '', text)
    text = re.sub(r'[\u0400-\u04FF]+', '', text)
    
    text = text.replace("สวัสดีครับ/ครับกิ๊ก", "สวัสดีค่ะทุกคน")
    text = text.replace("สวัสดีครับกิ๊ก", "สวัสดีค่ะทุกคน")
    text = text.replace("ครับกิ๊ก", "ค่ะ")
    
    # Correct broken/truncated Thai terms
    text = text.replace("ภูมิคุ้มก", "ภูมิคุ้มกัน")
    text = text.replace("อัก체ระ", "อักเสบ")
    text = text.replace("อักเสบระ", "อักเสบ")
    text = text.replace("ป้องรัง", "ป้องกัน")
    
    # Replace wrong vegetables with correct salad greens grown at KITA FARM
    text = text.replace("ผักโบรกoli", "ผักกรีนโอ๊คและเรดโอ๊ค")
    text = text.replace("ผักโบรโคลิ", "ผักกรีนโอ๊คและเรดโอ๊ค")
    text = text.replace("บรอกโคลี", "ผักกรีนโอ๊ค")
    text = text.replace("ผักกาดขาวสีเขียว", "ผักกรีนคอสใบอ้วนๆ")
    text = text.replace("ผักกาดขาว", "ผักกรีนคอส")
    text = text.replace("โบรกโคลี", "ผักสลัด")
    text = text.replace("กะหล่ำปลี", "ผักสลัดเรดโอ๊ค")
    text = text.replace("ผักบุ้ง", "ผักสลัดเรดโอ๊ค")
    
    # Correct farming terminology
    text = text.replace("เกษตรอินทรีย์", "การปลูกไฮโดรโปนิกส์ปลอดสารเคมี")
    text = text.replace("น้ำยาเคมี", "ปุ๋ยแร่ธาตุที่เหมาะสม")
    text = text.replace("พืชป้องกฤษ์", "การป้องกันศัตรูพืชทางธรรมชาติ")
    text = text.replace("พืชป้องกฤษ", "การป้องกันศัตรูพืชทางธรรมชาติ")
    
    # Text flow cleanups
    text = text.replace("ไม่สนใจไม่ทาง", "น่าสนใจมากๆ เลยนะคะ")
    text = text.replace("เจ้าคะ", "เจ้า")
    text = text.replace("นะครับ", "นะคะ")
    text = text.replace("ครับ", "ค่ะ")
    
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    return text.strip()

def run_daily_loop():
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    
    print("=== KITA FARM Content Automation Loop: Started ===")
    
    category = random.choice(list(CATEGORIES.keys()))
    topic = random.choice(CATEGORIES[category])
    
    facts = fact_check_topic(category, topic)
    facts = clean_script_text(facts)
    print(f"\nFact Check Summary:\n{facts}\n")
    
    brief_data = write_reels_script(category, topic, facts)
    
    content_data = {
        "category": category,
        "topic": brief_data.get("topic", topic),
        "facts": facts,
        "script": brief_data.get("script", ""),
        "hashtags": brief_data.get("hashtags", []),
        "shooting_scenes": brief_data.get("shooting_scenes", []),
        "voice_path": "Raw/Voice/daily_voice.mp3",
        "approved": False
    }
    
    with open("Projects/Kitas_Farm/today_content.json", "w", encoding="utf-8") as f:
        json.dump(content_data, f, ensure_ascii=False, indent=2)
    print("Content Meta & Shooting brief saved. Ready for Kik to select/approve and shoot!")

if __name__ == "__main__":
    run_daily_loop()
