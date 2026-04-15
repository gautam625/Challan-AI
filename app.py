import os
import re
import cv2
import pytesseract
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

# ---------------- SESSION ----------------
st.session_state.setdefault("page", "Dashboard")
st.session_state.setdefault("action_done", None)
st.session_state.setdefault("last_plate", None)

# ---------------- OCR FUNCTIONS ----------------
def preprocess_plate(plate):
    gray = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
    kernel = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
    gray = cv2.filter2D(gray, -1, kernel)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    thresh = cv2.adaptiveThreshold(gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY, 11, 2)
    return gray, thresh

def fix_format(text):
    text = re.sub('[^A-Z0-9]', '', text.upper())
    if len(text) < 8:
        return text
    text = list(text)
    for i in range(len(text)):
        if i in [0,1,4,5]:
            if text[i] == '0': text[i] = 'O'
            if text[i] == '1': text[i] = 'I'
            if text[i] == '8': text[i] = 'B'
        if i in [2,3,6,7,8,9]:
            if text[i] == 'O': text[i] = '0'
            if text[i] == 'I': text[i] = '1'
            if text[i] == 'B': text[i] = '8'
            if text[i] == 'Z': text[i] = '2'
    return ''.join(text)

def extract_text(plate):
    gray, thresh = preprocess_plate(plate)
    configs = [
        r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    ]
    results = []
    for config in configs:
        t1 = pytesseract.image_to_string(gray, config=config)
        t2 = pytesseract.image_to_string(thresh, config=config)
        results.extend([t1, t2])
    return results

def clean_plate(text_list):
    candidates = []
    for text in text_list:
        text = fix_format(text)
        match = re.search(r'[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}', text)
        if match:
            candidates.append(match.group())
    if candidates:
        return max(set(candidates), key=candidates.count)
    best = ""
    for t in text_list:
        t = re.sub('[^A-Z0-9]', '', t.upper())
        if len(t) > len(best):
            best = t
    return best if best else "UNKNOWN"

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")

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
        df = pd.DataFrame(data, columns=["ID","Car Number","Amount","Reason","Date","Status"])
        col1,col2,col3 = st.columns(3)
        col1.markdown(f"#### 🚘 Total Challans \n#### {len(df)}")
        col2.markdown(f"#### 💰 Total Amount \n##### ₹ {df['Amount'].sum()}")
        col3.markdown(f"#### ⏳ Pending \n#### {len(df[df['Status']=='Pending'])}")
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
    file = st.file_uploader("Upload image")

    if file:
        image = Image.open(file)
        img = np.array(image)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cascade = cv2.CascadeClassifier("haarcascade_russian_plate_number.xml")
        plates = cascade.detectMultiScale(gray,1.1,4)
        if len(plates)==0:
            st.error("No plate found")
        else:
            x,y,w,h = plates[0]
            cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)
            image_box = Image.fromarray(img)
            plate = img[y:y+h,x:x+w]
            texts = extract_text(plate)
            car_number = clean_plate(texts)
            match = re.search(r'[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}', car_number)
            if not match:
                st.error("Invalid plate")
                st.stop()
            car_number = match.group(0)
            owner = get_owner(car_number)
            if st.session_state.last_plate != car_number:
                st.session_state.action_done = None
                st.session_state.last_plate = car_number

            col1,col2 = st.columns(2)

            with col1:
                st.image(image_box,width=250)
                st.markdown(f"## 🚗 {car_number}")
                if owner:
                    st.markdown(f"- **Name:** {owner[1]}\n- **Age:** {owner[2]}\n- **Place:** {owner[3]}\n- **Mobile:** {owner[4]}")

            with col2:
                st.markdown("## 🚨 Challan Details")
                fine_map = {"Wrong Parking":500,"Over-speeding":1000,"Signal Jumping":500,"Without License":1000,"Drunken Driving":500}
                reason = st.selectbox("Reason",list(fine_map.keys()))
                fine = fine_map[reason]

                date = datetime.now().strftime("%d-%m-%Y")
                time = datetime.now().strftime("%I:%M %p")

                pending = sum(row[0] for row in get_pending_challans(car_number))
                total = fine + pending

                st.write(f"💰 Fine: {fine}")
                st.write(f"📅 Datte: {date}")
                st.write(f"⏰ Time: {time}")
                st.write(f"Pending: {pending}")
                st.write(f"##### Total Amount : {total}")

            # -------- BUTTON LOGIC FINAL --------
            if owner:
                if st.session_state.action_done is None:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🚨 Issue Challan"):
                            insert_challan(car_number, fine, reason,str(datetime.now().date()), "Pending")
                            st.session_state.action_done = "issue"
                            st.rerun()
                    with col2:
                        if st.button("💳 Pay Challan"):
                            insert_challan(car_number, fine, reason,str(datetime.now().date()), "Paid")
                            st.session_state.action_done = "pay"
                            st.rerun()
                else:
                    if st.session_state.action_done == "issue":
                        st.success("✅ Challan issued successfully . But Pending...")
                    elif st.session_state.action_done == "pay":
                        st.success("✅ Challan paid successfully")

            st.markdown("---")
            
            colA,colB = st.columns(2)

            with colA:
                if owner:
                    if st.button("📞 Send WhatsApp"):
                        mobile = owner[4]
                        if not re.match(r'^[6-9][0-9]{9}$', mobile):
                            st.error("❌ Mobile number incorrect")
                        else:
                            try:
                                sid = send_msg(owner, car_number, reason,fine,pending,total,date, time)
                                st.success("✅ WhatsApp Sent Successfully")
                            except Exception:
                                st.error("❌ Failed to send WhatsApp. Check number or network.")
                else:
                    st.warning("⚠️ Owner not registered — cannot send WhatsApp.")
                    if st.button("➕ Register Vehicle"):
                        st.session_state.page = "Register Vehicle"
                        st.session_state.prefill_car = car_number
                        st.rerun()

            with colB:
                if owner:
                    temp="temp.png"
                    image_box.save(temp)
                    pdf_bytes = generate_pdf(car_number,owner,reason,fine,pending,total,date,time,temp)
                    st.download_button("📄 Download PDF",pdf_bytes,f"{car_number}.pdf")
                    os.remove(temp)

# ---------------- REGISTER ----------------
elif st.session_state.page == "Register Vehicle":
    st.title("➕ Register Vehicle")
    col1,col2 = st.columns(2)

    car_no = col1.text_input("🚗 Car Number",value=st.session_state.get("prefill_car",""))
    location = col2.text_input("📍 Location")
    name = col1.text_input("👤 Owner Name")
    mobile = col2.text_input("📱 Mobile")
    age = st.number_input("🎂 Age",18,100)

    if st.button("Register Vehicle"):
        insert_data(car_no.upper(),name,age,location,mobile)
        st.success("Registered")
        st.session_state.pop("prefill_car",None)

# ---------------- DATABASE ----------------
elif st.session_state.page == "Vehicle Database":
    st.title("🚘 Vehicle Database")
    data = get_all_vehical()
    if data:
        df = pd.DataFrame(data,columns=["Car Number","Owner Name","Age","Location","Mobile"])
        st.dataframe(df)
    else:
        st.warning("No data found")
