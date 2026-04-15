import os
import re
import cv2
import easyocr
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image
from datetime import datetime

# Database
from database import create_db, insert_data, get_owner, get_all_vehical, get_all_challans, insert_challan, get_pending_challans
from whatsapp import send_msg
from pdf import generate_pdf
create_db()

# ✅ Load EasyOCR once — no Tesseract needed
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")

# ---------------- SESSION ----------------
st.session_state.setdefault("page", "Dashboard")

# ---------------- SIDEBAR ----------------
st.sidebar.markdown("# 🚗 Challan-AI")
menu = [("Dashboard", "🏠"), ("Issue Challan", "📸"), ("Vehicle Database", "🚘"), ("Register Vehicle", "➕")]
for label, icon in menu:
    if st.sidebar.button(f"{icon} {label}", width="stretch"):
        st.session_state.page = label

# ---------------- DASHBOARD ----------------
if st.session_state.page == "Dashboard":
    st.title("📊 Dashboard")
    data = get_all_challans()
    if data:
        df = pd.DataFrame(data, columns=["ID", "Car Number", "Amount", "Reason", "Date", "Status"])
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"""#### 🚘 Total Challans \n  #### {len(df)}""")
        col2.markdown(f"""#### 💰 Total Amount \n ##### ₹ {df['Amount'].sum()}""")
        col3.markdown(f"""#### ⏳ Pending \n #### {len(df[df["Status"] == "Pending"])}""")
        st.markdown("---")
        search = st.text_input("🔍 Search by Car Number")
        if search:
            df = df[df["Car Number"].str.contains(search, case=False)]
        st.dataframe(df, width="stretch", height=400)
    else:
        st.info("No challans issued yet.")

# ---------------- ISSUE CHALLAN ----------------
elif st.session_state.page == "Issue Challan":
    st.title("📸 Issue Challan")
    file = st.file_uploader("Upload image to detect vehicle and generate challan")

    if file:
        image = Image.open(file)
        img = np.array(image)

        # Convert to BGR for OpenCV
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        cascade = cv2.CascadeClassifier("haarcascade_russian_plate_number.xml")
        plates = cascade.detectMultiScale(gray, 1.1, 4)

        if len(plates) == 0:
            st.error("❌ No number plate found. Please upload a clearer image.")
        else:
            x, y, w, h = plates[0]

            # Draw rectangle on original image
            img_display = img.copy()
            cv2.rectangle(img_display, (x, y), (x + w, y + h), (255, 0, 0), 2)
            image_box = Image.fromarray(img_display)

            # Crop plate region
            plate_crop = gray[y:y + h, x:x + w]

            # ✅ EasyOCR reads the plate
            with st.spinner("Reading number plate..."):
                results = reader.readtext(plate_crop, detail=0, allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')

            raw_text = ''.join(results).upper()
            clean_text = ''.join(filter(str.isalnum, raw_text))

            # Match Indian number plate format: e.g. TS09AB1234
            match = re.search(r'[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}', clean_text)

            if not match:
                st.error(f"❌ Could not read plate clearly. OCR got: `{clean_text}` — try a clearer image.")
                st.stop()

            car_number = match.group(0)
            owner = get_owner(car_number)

            col1, col2 = st.columns(2)

            with col1:
                st.image(image_box, width=250, caption="Detected Plate")
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
                    "Drunken Driving": 500
                }
                reason = st.selectbox("Reason", list(fine_map.keys()))
                fine = fine_map[reason]
                st.write(f"###### 💰 Fine: Rs. {fine}")

                date = datetime.now().strftime("%d-%m-%Y")
                time = datetime.now().strftime("%I:%M %p")
                st.write("📅 **Date:**", date)
                st.write("⏰ **Time:**", time)

                pending_data = get_pending_challans(car_number)
                total_pending = sum(row[0] for row in pending_data)
                st.write(f"###### 📋 Pending Challans: Rs. {total_pending}")

                grand_total = fine + total_pending
                st.write(f"##### 🧾 Total Amount: Rs. {grand_total}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚨 Issue Challan"):
                    insert_challan(car_number=car_number, amount=fine, reason=reason,
                                   date=str(datetime.now().date()), status="Pending")
                    st.success("✅ Challan Issued Successfully")
            with col2:
                if st.button("💳 Pay Challan"):
                    insert_challan(car_number=car_number, amount=fine, reason=reason,
                                   date=str(datetime.now().date()), status="Paid")
                    st.success("✅ Challan Paid Successfully")

            st.markdown("---")
            colA, colB = st.columns(2)

            with colA:
                if owner:
                    if st.button("📞 Send WhatsApp"):
                        try:
                            sid = send_msg(owner, car_number, reason, fine, total_pending, grand_total, date, time)
                            st.success(f"✅ WhatsApp Sent! SID: {sid}")
                        except Exception as e:
                            st.error(f"❌ Failed: {str(e)}")
                else:
                    st.warning("⚠️ Owner not registered — cannot send WhatsApp.")

            with colB:
                if owner:
                    temp_path = "temp.png"
                    image_box.save(temp_path)
                    pdf_bytes = generate_pdf(car_number, owner, reason, fine, total_pending, grand_total, date, time, temp_path)
                    st.download_button(
                        label="📄 Download PDF",
                        data=pdf_bytes,
                        file_name=f"{car_number}_challan.pdf",
                        mime="application/pdf"
                    )
                    os.remove(temp_path)

# ---------------- DATABASE ----------------
elif st.session_state.page == "Vehicle Database":
    st.title("🚘 Vehicle Database")
    data = get_all_vehical()
    if data:
        df = pd.DataFrame(data, columns=["Car Number", "Owner Name", "Age", "Location", "Mobile"])
        st.dataframe(df, width="stretch")
    else:
        st.warning("No vehicle records found")

# ---------------- REGISTER VEHICLE ----------------
elif st.session_state.page == "Register Vehicle":
    st.title("➕ Register Vehicle")
    col1, col2 = st.columns(2)
    car_no = col1.text_input("🚗 Car Number")
    location = col2.text_input("📍 Location")
    name = col1.text_input("👤 Owner Name")
    mobile = col2.text_input("📱 Mobile")
    age = st.number_input("🎂 Age", 18, 100)
    if st.button("Register Vehicle"):
        insert_data(car_no.upper(), name, age, location, mobile)
        st.success("✅ Vehicle Registered")
