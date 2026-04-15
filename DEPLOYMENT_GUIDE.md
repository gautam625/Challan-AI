# 🚗 Challan-AI — Setup & Deployment Guide

---

## 📁 Files Overview

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit UI |
| `database.py` | SQLite DB functions |
| `whatsapp.py` | Twilio WhatsApp integration |
| `pdf.py` | PDF challan generator |
| `requirements.txt` | Python dependencies |
| `haarcascade_russian_plate_number.xml` | Number plate detection model |
| `.env` | Your secret credentials (never commit this!) |
| `Dockerfile` | Docker image definition |
| `docker-compose.yml` | Easy Docker orchestration |
| `.dockerignore` | Keeps image clean |

---

## 🐳 — Docker Deployment

### Prerequisites
- Docker Desktop installed: https://www.docker.com/products/docker-desktop/

### Option A: Using Docker Compose (Recommended)

```bash
# 1. Make sure your .env file exists with Twilio credentials
# (Docker Compose reads it automatically)

# 2. Build and start
docker-compose up --build

# App runs at: http://localhost:8501

# 3. Stop
docker-compose down

# To rebuild after code changes:
docker-compose up --build --force-recreate
```

### Option B: Plain Docker (without Compose)

```bash
# 1. Build the image
docker build -t challan-ai .

# 2. Run with env variables
docker run -p 8501:8501 \
  -e TWILIO_ACCOUNT_SID=your_sid \
  -e TWILIO_AUTH_TOKEN=your_token \
  -e TWILIO_FROM_NUMBER="whatsapp:+14155238886" \
  -v challan_data:/data \
  challan-ai
```

---

## ☁️ PART 3 — Deploy to Render with Docker

1. Push your project to GitHub (make sure `.env` is in `.gitignore`!)

2. Go to https://render.com → **New** → **Web Service**

3. Connect your GitHub repo

4. Choose **"Docker"** as the environment (NOT Python)

5. In Render dashboard → **Environment** tab, add these variables:
   ```
   TWILIO_ACCOUNT_SID    = ACxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN     = your_auth_token
   TWILIO_FROM_NUMBER    = whatsapp:+14155238886
   ```

6. For persistent database, go to **Disks** tab:
   - Mount path: `/data`
   - Size: 1 GB (free tier)

7. Click **Deploy** — Render will build the Docker image automatically.

---

## ⚠️ Important Notes

- **Never commit `.env`** to GitHub. Add it to `.gitignore`.
- The SQLite DB is stored at `/data/cars.db` inside Docker. Using a volume (`-v challan_data:/data`) ensures data survives container restarts.
- On Render free tier, the container sleeps after inactivity — first request after sleep may take ~30 seconds.

---

## 🐛 Common Issues

| Problem | Fix |
|---------|-----|
| `tesseract not found` | Dockerfile installs it — make sure you're using Docker, not bare Python on server |
| `No plate found` | Upload a clear, well-lit image of the number plate |
| `WhatsApp not sending` | Check Twilio credentials in environment variables |
| DB data lost on restart | Make sure Docker volume is configured (see docker-compose.yml) |
