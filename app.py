import os
import re
import cv2
import pytesseract
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image
from datetime import datetime


if os.name == "nt":  # Windows
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    os.environ['TESSDATA_PREFIX'] = r"C:\Program Files\Tesseract-OCR\tessdata"
else:  # Render (Linux)
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

import os
print(os.system("tesseract --version"))

# Database
from database import create_db, insert_data, get_owner, get_all_vehical, get_all_challans, insert_challan, get_pending_challans
from whatsapp import send_msg
from pdf import generate_pdf
create_db()

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

        # 🔍 Search
        search = st.text_input("🔍 Search by Car Number")
        if search:
            df = df[df["Car Number"].str.contains(search, case=False)]

        # 📋 Table
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
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cascade = cv2.CascadeClassifier("haarcascade_russian_plate_number.xml")
        plates = cascade.detectMultiScale(gray, 1.1, 4)

        if len(plates) == 0:
            st.error("No plate found")
        else:
            x, y, w, h = plates[0]

            # 🔥 Draw rectangle
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            image_box = Image.fromarray(img)

            # Crop plate
            plate = gray[y:y + h, x:x + w]

            # OCR
            text = pytesseract.image_to_string(plate, config='--psm 7')
            text = ''.join(filter(str.isalnum, text.upper()))

            match = re.search(r'[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}', text)

            if not match:
                st.error("Invalid plate. Upload clear image.")
                st.stop()

            car_number = match.group(0)
            owner = get_owner(car_number)

            col1, col2 = st.columns(2)

            # LEFT SIDE
            with col1:
                st.image(image_box, width=250)
                st.markdown(f"## 🚗 {car_number}")
                if owner:
                    st.markdown(f"""- **Name:** {owner[1]}\n- **Age:** {owner[2]}\n- **Place:** {owner[3]}\n- **Mobile:** {owner[4]}""")

            # RIGHT SIDE
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
                st.write("⏰  **Time:**", time)

                pending_data = get_pending_challans(car_number)
                pending_amounts = [row[0] for row in pending_data]
                total_pending = sum(pending_amounts)
                st.write(f"###### 📋 Pending Challans: Rs. {total_pending}")

                grand_total = fine + total_pending
                st.write(f"##### 🧾 Total Amount: Rs. {grand_total}")

            col1, col2 = st.columns(2)

            # LEFT BUTTON (Issue Challan)
            with col1:
                if st.button("🚨 Issue Challan"):
                    insert_challan(car_number=car_number, amount=fine, reason=reason,
                                   date=str(datetime.now().date()), status="Pending")
                    st.success("✅ Challan Issued Successfully")

            # RIGHT BUTTON (Pay Challan)
            with col2:
                if st.button("💳 Pay Challan"):
                    insert_challan(car_number=car_number, amount=fine, reason=reason,
                                   date=str(datetime.now().date()), status="Paid")
                    st.success("✅ Challan Paid Successfully")

            st.markdown("---")

            colA, colB = st.columns(2)

            # ✅ WhatsApp via Twilio
            with colA:
                if owner:
                    if st.button("📞 Send WhatsApp"):
                        try:
                            sid = send_msg(owner, car_number, reason, fine, total_pending, grand_total, date, time)
                            st.success(f"✅ WhatsApp Sent! Message SID: {sid}")
                        except Exception as e:
                            st.error(f"❌ Failed to send WhatsApp: {str(e)}")
                else:
                    st.warning("⚠️ Owner not registered — cannot send WhatsApp.")

            # PDF Download
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
        st.success("Vehicle Registered")
