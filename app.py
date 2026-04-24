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
คุณคือ "น้องแสนสุข" ผู้ช่วย AI ของโครงการบำบัดน้ำเสียรวม เทศบาลเมืองแสนสุข จังหวัดชลบุรี

=== ข้อมูลโครงการ ===
ชื่อโครงการ: โครงการจ้างเหมาเอกชนบริหารจัดการระบบบำบัดน้ำเสียรวม เทศบาลเมืองแสนสุข จังหวัดชลบุรี
สัญญาเลขที่: 1/2569 ลงวันที่ 30 กันยายน 2568
วันเริ่มสัญญา: 1 ตุลาคม 2568 / วันสิ้นสุดสัญญา: 30 กันยายน 2569
ผู้รับจ้าง: บริษัท เจม เอ็นไวรันเมนทัล แมเนจเม้นท์ จำกัด
มูลค่างาน: 2,615,500 บาท (รวมภาษีมูลค่าเพิ่ม)

=== คณะกรรมการตรวจรับพัสดุ ===
1. นายชัชวาล กอหญ้ากลาง - ประธาน
2. นางสาวเพ็ญศรี ชายชาญณรงค์ - กรรมการ
3. นายณรงค์ศักดิ์ กลิ่นขจร - กรรมการ

=== รายงานผลการดำเนินการ มีนาคม 2569 (งวดที่ 6) ===
ปริมาณน้ำเสียรวมเข้าระบบ: 467,240 ลบ.ม. (เหนือ 258,120 / ใต้ 209,138)
ปริมาณการใช้ไฟฟ้า: 69,000 กิโลวัตต์ชั่วโมง
ปริมาณน้ำประปา: 466.85 ลบ.ม.
น้ำรดต้นไม้: 4,573 ลบ.ม. (459 เที่ยว)

=== คุณภาพน้ำ มีนาคม 2569 ===
แสนสุขเหนือ: pH 6.66/6.55, อุณหภูมิ 27.25/27.55C, DO 2.05/3.81 mg/L (ผ่านมาตรฐาน)
แสนสุขใต้: pH 7.15/7.14, อุณหภูมิ 29.16/28.35C, DO 2.91/4.15 mg/L (ผ่านมาตรฐาน)

=== ประสิทธิภาพบำบัด ===
แสนสุขเหนือ: BOD 45%, TSS 49%, Oil&Grease 75%
แสนสุขใต้: BOD 49%, TSS 34%, Oil&Grease 90%
หมายเหตุ: แสนสุขใต้ BOD/TSS ไม่ผ่านมาตรฐาน เนื่องจาก Sludge Bulking และถัง Clarifier ชำรุด

=== สถานะเครื่องจักร ===
แสนสุขเหนือ: 117 รายการ ใช้งานได้ 30 รายการ
แสนสุขใต้: 92 รายการ ใช้งานได้ 19 รายการ
งานบำรุงรักษา: เหนือ 54 งาน / ใต้ 42 งาน

=== ค่าจ้างงวดที่ 6 ===
ค่าจ้าง: 203,621.50 บาท + VAT 7% = รวม 217,875.00 บาท
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
                "model": "llama3-70b-8192",
                "messages": [
                    {"role": "system", "content": f'คุณคือ "น้องแสนสุข" ผู้ช่วย AI ตอบเป็นภาษาไทย กระชับ เป็นมิตร ใช้ข้อมูลนี้ตอบ:\n{KNOWLEDGE_BASE}'},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.3,
                "max_tokens": 800
            },
            timeout=30
        )
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error: {str(e)}"

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data()
    if not verify_signature(body, signature):
        abort(400)
    for event in json.loads(body).get("events", []):
        if event.get("type") == "message" and event["message"].get("type") == "text":
            reply_message(event["replyToken"], ask_groq(event["message"]["text"]))
    return "OK", 200

@app.route("/", methods=["GET"])
def health():
    return "น้องแสนสุข Bot is running! 🌊", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
