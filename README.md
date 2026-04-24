# น้องแสนสุข LINE Bot 🌊

LINE Bot ผู้ช่วย AI สำหรับโครงการบำบัดน้ำเสียเทศบาลเมืองแสนสุข  
ขับเคลื่อนด้วย Groq (LLaMA 3 70B) + LINE Messaging API

---

## 📁 โครงสร้างไฟล์
```
saensuk-bot/
├── app.py            # ตัวหลัก Flask + LINE webhook + Groq
├── requirements.txt  # Python dependencies
├── render.yaml       # Render deploy config
└── README.md
```

---

## 🚀 วิธี Deploy บน Render + GitHub

### ขั้นตอนที่ 1 – อัปโหลดขึ้น GitHub
```bash
git init
git add .
git commit -m "initial: น้องแสนสุข LINE Bot"
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO>.git
git push -u origin main
```

### ขั้นตอนที่ 2 – สร้าง Web Service บน Render
1. ไปที่ https://render.com → **New → Web Service**
2. เชื่อม GitHub repository ที่สร้างไว้
3. Render จะอ่าน `render.yaml` อัตโนมัติ

### ขั้นตอนที่ 3 – ตั้ง Environment Variables บน Render
| Key | ค่า |
|-----|-----|
| `LINE_CHANNEL_SECRET` | จาก LINE Developers Console |
| `LINE_CHANNEL_ACCESS_TOKEN` | จาก LINE Developers Console |
| `GROQ_API_KEY` | จาก https://console.groq.com |

### ขั้นตอนที่ 4 – ตั้ง Webhook URL ใน LINE Developers
1. ไปที่ LINE Developers Console → Channel ของคุณ
2. **Messaging API → Webhook URL**
3. ใส่: `https://<your-render-app>.onrender.com/webhook`
4. กด **Verify** แล้ว **Enable Webhook**

---

## ➕ เพิ่มข้อมูลใหม่

เปิดไฟล์ `app.py` แล้วเพิ่มข้อมูลในส่วน `KNOWLEDGE_BASE`:

```python
KNOWLEDGE_BASE = """
...
=== ข้อมูลใหม่ที่ต้องการเพิ่ม ===
เนื้อหา...
"""
```

รองรับ: Excel, PowerPoint, Word, PDF – แค่แปลงเป็นข้อความแล้ว paste เพิ่มในส่วนนี้

---

## 💬 ตัวอย่างคำถามที่ตอบได้
- "ปริมาณน้ำเสียเดือนมีนาคมเป็นเท่าไหร่?"
- "คุณภาพน้ำเป็นอย่างไรบ้าง?"
- "เครื่องจักรมีปัญหาอะไร?"
- "ค่าจ้างงวดที่ 6 เท่าไหร่?"
- "ใครเป็นคณะกรรมการตรวจรับพัสดุ?"
