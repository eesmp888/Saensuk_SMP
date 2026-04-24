import os
import json
import hashlib
import hmac
import base64
import requests
from flask import Flask, request, abort

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

KNOWLEDGE_BASE = """
=== ข้อมูลโครงการ ===
ชื่อโครงการ: โครงการจ้างเหมาเอกชนบริหารจัดการระบบบำบัดน้ำเสียรวม เทศบาลเมืองแสนสุข จังหวัดชลบุรี
สัญญาเลขที่: 1/2569 ลงวันที่ 30 กันยายน 2568
วันเริ่มสัญญา: 1 ตุลาคม 2568 / วันสิ้นสุดสัญญา: 30 กันยายน 2569
ผู้รับจ้าง: บริษัท เจม เอ็นไวรันเมนทัล แมเนจเม้นท์ จำกัด (GEM)
มูลค่างาน: 2,615,500 บาท (รวมภาษีมูลค่าเพิ่ม)
คณะกรรมการตรวจรับพัสดุ: 1.นายชัชวาล กอหญ้ากลาง (ประธาน) 2.นางสาวเพ็ญศรี ชายชาญณรงค์ 3.นายณรงค์ศักดิ์ กลิ่นขจร

=== รายงานมีนาคม 2569 (งวดที่ 6) ===
น้ำเสียรวม: 467,240 ลบ.ม. (เหนือ 258,120 / ใต้ 209,138)
ไฟฟ้า: 69,000 kWh / น้ำประปา: 466.85 ลบ.ม. / น้ำรดต้นไม้: 4,573 ลบ.ม.
คุณภาพน้ำเหนือ: pH 6.66/6.55, Temp 27.25/27.55C, DO 2.05/3.81 (ผ่าน)
คุณภาพน้ำใต้: pH 7.15/7.14, Temp 29.16/28.35C, DO 2.91/4.15 (ผ่าน)
BOD เหนือ 45% / ใต้ 49% (ใต้ไม่ผ่านมาตรฐาน เนื่องจาก Sludge Bulking และ Clarifier ชำรุด)
ค่าจ้างงวดที่ 6: 203,621.50 + VAT = 217,875.00 บาท

=== สถานะเครื่องจักร ณ 31 มี.ค. 2569 ===
แสนสุขเหนือ (117 รายการ):
- สถานีแหลมแท่น: Pump No.1 ปกติ / No.2 ส่งซ่อม / No.3 ชำรุด
- บางแสนสาย2: Pump No.2 ปกติ / No.1,3 ชำรุด
- สุขุมวิท: Pump No.1,2,3 เครื่อง+ควบคุมชำรุด
- โรงเหนือ: Pump No.3 ปกติ / No.1,4 ชำรุดถาวร / No.2 ปั๊มปกติตู้ชำรุด
- Aerator ปกติ: No.2,3,7,9,12,14 / ชำรุด: No.1,4,5,6,8,10,11,13,15,16
- Clarifier No.1,2,8,9: ชำรุด
- หม้อแปลง 1,000 kVA: น้ำมันรั่ว

แสนสุขใต้ (92 รายการ):
- หาดวอนนภา: WW Pump No.1,2 ปกติ / No.3 เครื่องชำรุด / EFF Pump No.2 ปกติ / No.1,3 เครื่องชำรุด
- โรงใต้: Aerator No.3,7 ปกติ / No.1 ควบคุมชำรุด / No.2,4,5,6,8 ชำรุดถาวร / No.9-16 ไม่พบ/ชำรุด
- Clarifier No.1,2: ชำรุด
- หม้อแปลง 1,000 kVA: น้ำมันรั่ว

=== งานซ่อมบำรุง มีนาคม 2569 ===
เหนือ: บำรุงรักษา 54 งาน / ใต้: 42 งาน
งานคงค้าง: 1.ปั้มระบายน้ำฝน No.1 ฐานปากแตรชำรุด 2.ปั๊มระบายน้ำฝน No.3 สายไฟพันกันร้อนเกิน Trip 10/9/68

=== เรื่องติดตาม ===
1. ชุดควบคุม Jet Aerator ทั้งสองโรง - อยู่ระหว่างจัดซื้อ (จัดส่งบางส่วนแล้ว)
2. ชุดควบคุม Waste Water Pump No.2 โรงเหนือ - ซ่อม 4 ชุด อยู่ระหว่างทดสอบก่อนติดตั้ง

=== Runhour เครื่องจักรสำคัญ โรงเหนือ (มีนาคม 2569) ===
Jet Aerator No.2: 22,509 ชม / No.3: 9,955 ชม / No.7: 13,837 ชม
Jet Aerator No.12: 94,424 ชม / No.14: 87,020 ชม / No.15: 99,065 ชม
Clarifier เหนือ: 16,339 / 68,846 / 64,496 / 56,077 ชม
"""

def verify_signature(body, signature):
    hash_val = hmac.new(LINE_CHANNEL_SECRET.encode("utf-8"), body, hashlib.sha256).digest()
    return hmac.compare_digest(base64.b64encode(hash_val).decode("utf-8"), signature)

def reply_message(reply_token, text):
    requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"},
        json={"replyToken": reply_token, "messages": [{"type": "text", "text": text}]}
    )

def ask_groq(user_message):
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": f'คุณคือ "น้องแสนสุข" ผู้ช่วย AI ตอบเป็นภาษาไทย กระชับ เป็นมิตร ใช้ข้อมูล:\n{KNOWLEDGE_BASE}'},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.3,
                "max_tokens": 300
            },
            timeout=30
        )
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error: {str(e)}"

TRIGGER_WORDS = ["น้องแสนสุข", "แสนสุข"]

def should_reply(event):
    source_type = event.get("source", {}).get("type", "user")
    text = event["message"]["text"]
    if source_type == "user":
        return True
    if source_type in ["group", "room"]:
        mention = event["message"].get("mention", {})
        if mention.get("mentionees"):
            return True
        for word in TRIGGER_WORDS:
            if word in text:
                return True
        return False
    return True

def clean_text(event):
    text = event["message"]["text"]
    for word in TRIGGER_WORDS:
        text = text.replace(word, "").strip()
    return text if text else event["message"]["text"]

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data()
    if not verify_signature(body, signature):
        abort(400)
    for event in json.loads(body).get("events", []):
        if event.get("type") == "message" and event["message"].get("type") == "text":
            if should_reply(event):
                reply_message(event["replyToken"], ask_groq(clean_text(event)))
    return "OK", 200

@app.route("/", methods=["GET"])
def health():
    return "น้องแสนสุข Bot is running! 🌊", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
