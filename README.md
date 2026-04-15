# 🚗 Challan-AI

### AI-Powered Traffic Challan Management System

Challan-AI is an intelligent web application that automatically detects vehicle number plates from images and generates traffic challans in real time. It integrates OCR, database management, WhatsApp notifications, and PDF generation into a single streamlined system.

---

🌐 Live Demo: https://challan-ai-1-yuvn.onrender.com

---

## 📸 Screenshots
<img width="3056" height="1558" alt="image" src="https://github.com/user-attachments/assets/0462583e-e48b-4968-be31-be02ecb37c9f" />

<img width="3090" height="1572" alt="Screenshot 2026-04-16 002038" src="https://github.com/user-attachments/assets/656bc290-b940-47c0-b038-b64e7203d2a1" />

<img width="1654" height="1136" alt="image" src="https://github.com/user-attachments/assets/3f2e0467-7bd0-4e92-945e-bff9e51511b4" />

---

## 📌 Features

* 🔍 **Automatic Number Plate Detection**

  * Detects vehicle plates using OpenCV Haar Cascade
  * Enhanced OCR with preprocessing for higher accuracy

* 🤖 **Smart OCR Pipeline**

  * Multi-pass Tesseract OCR
  * Noise reduction, sharpening, thresholding
  * Indian number plate format correction

* 📄 **Instant Challan Generation**

  * Generate challans with fine calculation
  * Supports multiple violation types

* 📲 **WhatsApp Notification**

  * Sends challan details directly to vehicle owner
  * Integrated with Twilio API

* 🧾 **PDF Download**

  * Generate downloadable challan receipt

* 🗂 **Vehicle Database**

  * Store and manage vehicle owner details
  * Search and filter records

* 📊 **Dashboard Analytics**

  * Total challans issued
  * Total amount collected
  * Pending challans overview

* ➕ **Quick Registration Flow**

  * Auto-fill vehicle number if not registered
  * Seamless user experience

---

## 🛠 Tech Stack

| Technology    | Usage                  |
| ------------- | ---------------------- |
| Python        | Core backend logic     |
| Streamlit     | Web interface          |
| OpenCV        | Number plate detection |
| Tesseract OCR | Text recognition       |
| NumPy         | Image processing       |
| Pandas        | Data handling          |
| SQLite        | Database               |
| Twilio API    | WhatsApp messaging     |
| FPDF          | PDF generation         |

---

## ⚙️ Installation

### 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/challan-ai.git
cd challan-ai
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv env
env\Scripts\activate   # Windows
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Install Tesseract OCR

Download and install:
👉 https://github.com/tesseract-ocr/tesseract

Set path in code:

```python
pytesseract.pytesseract.tesseract_cmd = r"YOUR_PATH"
```

---

## ▶️ Run Application

```bash
streamlit run app.py
```

---

## 📂 Project Structure

```
challan-ai/
│
├── app.py
├── database.py
├── whatsapp.py
├── pdf.py
├── haarcascade_russian_plate_number.xml
├── requirements.txt
├── .env
└── README.md
```

---

## 🔐 Environment Variables

Create a `.env` file:

```
TWILIO_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_NUMBER=your_twilio_number
```

---

## 🚀 How It Works

1. Upload vehicle image
2. Detect number plate
3. Extract text using OCR
4. Validate plate format
5. Fetch owner details
6. Generate challan
7. Send WhatsApp notification
8. Download PDF receipt

---

## ⚠️ Limitations

* Works best with clear number plates
* Haar cascade may fail in extreme angles
* Requires Tesseract installation

---

## 🔮 Future Improvements

* YOLO-based number plate detection
* EasyOCR integration for higher accuracy
* Mobile app version
* Live CCTV integration
* Payment gateway integration

---

## 🤝 Contributing

Contributions are welcome!
Feel free to fork this repo and submit a pull request.

---

## 👨‍💻 Author

**Gautam Kumar**
AI Developer | Computer Vision Enthusiast

---

## ⭐ Support

If you like this project, give it a ⭐ on GitHub!

---
