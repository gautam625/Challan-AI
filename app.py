import os
import re
import cv2
import easyocr
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from database import create_db, insert_data, get_owner, get_all_vehical, get_all_challans, insert_challan, get_pending_challans
from whatsapp import send_msg
from pdf import generate_pdf

create_db()

# ✅ EasyOCR — loads once, no Tesseract needed
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

reader = load_ocr()

# ─────────────────────────────────────────
st.set_page_config(page_title="Challan AI", layout="wide")
st.session_state.setdefault("page", "Dashboard")

# ── SIDEBAR ──────────────────────────────
st.sidebar.markdown("# 🚗 Challan-AI")
for label, icon in [("Dashboard", "🏠"), ("Issue Challan", "📸"), ("Vehicle Database", "🚘"), ("Register Vehicle", "➕")]:
    if st.sidebar.button(f"{icon} {label}", use_container_width=True):
        st.session_state.page = label

page = st.session_state.page

# ── DASHBOARD ────────────────────────────
if page == "Dashboard":
    st.title("📊 Dashboard")
    data = get_all_challans()
    if data:
        df = pd.DataFrame(data, columns=["ID", "Car Number", "Amount", "Reason", "Date", "Status"])
        c1, c2, c3 = st.columns(3)
        c1.metric("🚘 Total Challans", len(df))
        c2.metric("💰 Total Amount", f"₹ {df['Amount'].sum()}")
        c3.metric("⏳ Pending", len(df[df["Status"] == "Pending"]))
        st.markdown("---")
        search = st.text_input("🔍 Search by Car Number")
        if search:
            df = df[df["Car Number"].str.contains(search, case=False)]
        st.dataframe(df, use_container_width=True, height=400)
    else:
        st.info("No challans issued yet.")

# ── ISSUE CHALLAN ─────────────────────────
elif page == "Issue Challan":
    st.title("📸 Issue Challan")
    file = st.file_uploader("Upload a vehicle image", type=["jpg", "jpeg", "png"])

    if file:
        image = Image.open(file).convert("RGB")
        img = np.array(image)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        cascade = cv2.CascadeClassifier("haarcascade_russian_plate_number.xml")
        plates = cascade.detectMultiScale(gray, 1.1, 4)

        if len(plates) == 0:
            st.error("❌ No number plate detected. Please upload a clearer image.")
        else:
            x, y, w, h = plates[0]
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            image_box = Image.fromarray(img)
            plate_crop = gray[y:y + h, x:x + w]

            # ── OCR ──
            with st.spinner("Reading number plate..."):
                results = reader.readtext(
                    plate_crop, detail=0,
                    allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                )
            raw = ''.join(results).upper()
            clean = ''.join(filter(str.isalnum, raw))
            match = re.search(r'[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}', clean)

            if not match:
                st.error(f"❌ Could not read plate. OCR result: `{clean}` — try a clearer image.")
                st.stop()

            car_number = match.group(0)
            owner = get_owner(car_number)

            # ── Display ──
            col1, col2 = st.columns(2)
            with col1:
                st.image(image_box, width=300, caption="Detected Plate")
                st.markdown(f"## 🚗 {car_number}")
                if owner:
                    st.markdown(f"""
- **Name:** {owner[1]}
- **Age:** {owner[2]}
- **Place:** {owner[3]}
- **Mobile:** {owner[4]}
""")
                else:
                    st.warning("⚠️ Vehicle not registered in database.")

            with col2:
                st.markdown("## 🚨 Challan Details")
                fine_map = {
                    "Wrong Parking": 500,
                    "Over-speeding": 1000,
                    "Signal Jumping": 500,
                    "Without License": 1000,
                    "Drunken Driving": 500,
                }
                reason = st.selectbox("Violation Reason", list(fine_map.keys()))
                fine = fine_map[reason]

                date = datetime.now().strftime("%d-%m-%Y")
                time = datetime.now().strftime("%I:%M %p")
                pending_data = get_pending_challans(car_number)
                total_pending = sum(r[0] for r in pending_data)
                grand_total = fine + total_pending

                st.write(f"💰 **Fine:** Rs. {fine}")
                st.write(f"📅 **Date:** {date}   ⏰ **Time:** {time}")
                st.write(f"📋 **Previous Pending:** Rs. {total_pending}")
                st.write(f"🧾 **Total Amount:** Rs. {grand_total}")

            # ── Action Buttons ──
            st.markdown("---")
            b1, b2, b3, b4 = st.columns(4)

            with b1:
                if st.button("🚨 Issue Challan", use_container_width=True):
                    insert_challan(car_number, fine, reason, str(datetime.now().date()), "Pending")
                    st.success("✅ Challan Issued!")

            with b2:
                if st.button("💳 Pay Challan", use_container_width=True):
                    insert_challan(car_number, fine, reason, str(datetime.now().date()), "Paid")
                    st.success("✅ Challan Paid!")

            with b3:
                if owner:
                    if st.button("📞 Send WhatsApp", use_container_width=True):
                        try:
                            sid = send_msg(owner, car_number, reason, fine, total_pending, grand_total, date, time)
                            st.success(f"✅ Sent! SID: {sid}")
                        except Exception as e:
                            st.error(f"❌ {str(e)}")
                else:
                    st.button("📞 Send WhatsApp", disabled=True, use_container_width=True)

            with b4:
                if owner:
                    temp_path = "temp.png"
                    image_box.save(temp_path)
                    pdf_bytes = generate_pdf(car_number, owner, reason, fine, total_pending, grand_total, date, time, temp_path)
                    st.download_button("📄 Download PDF", pdf_bytes, f"{car_number}_challan.pdf", "application/pdf", use_container_width=True)
                    os.remove(temp_path)

# ── VEHICLE DATABASE ──────────────────────
elif page == "Vehicle Database":
    st.title("🚘 Vehicle Database")
    data = get_all_vehical()
    if data:
        df = pd.DataFrame(data, columns=["Car Number", "Owner Name", "Age", "Location", "Mobile"])
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No vehicle records found.")

# ── REGISTER VEHICLE ──────────────────────
elif page == "Register Vehicle":
    st.title("➕ Register Vehicle")
    col1, col2 = st.columns(2)
    car_no   = col1.text_input("🚗 Car Number")
    location = col2.text_input("📍 Location")
    name     = col1.text_input("👤 Owner Name")
    mobile   = col2.text_input("📱 Mobile Number")
    age      = st.number_input("🎂 Age", 18, 100)

    if st.button("✅ Register Vehicle", use_container_width=True):
        if car_no and name and mobile and location:
            insert_data(car_no.upper(), name, age, location, mobile)
            st.success(f"✅ Vehicle {car_no.upper()} Registered Successfully!")
        else:
            st.error("❌ Please fill all fields.")
