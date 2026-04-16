import os
import re
import tempfile
from datetime import datetime

import cv2
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

from dotenv import load_dotenv
load_dotenv()

from ocr import detect_plate, read_plate
from pdf import generate_pdf
from whatsapp import send_whatsapp
from database import create_db,seed_default_data, upsert_vehicle, get_owner,get_all_vehicles, insert_challan,get_all_challans, get_pending_amount,get_dashboard_stats


# ── Bootstrap ─────────────────────────────────────────────────────────────────
create_db()
seed_default_data()

st.set_page_config(page_title="Challan-AI", layout="wide", page_icon="🚗")

PLATE_RE = re.compile(r'[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}')
PHONE_RE = re.compile(r'^[6-9][0-9]{9}$')
FINE_MAP = {"Wrong Parking":500, "Over-speeding":1000,"Signal Jumping":500,"Without License":1000,"Drunken Driving":2000,}

# ── Session state defaults ────────────────────────────────────────────────────
def _init_state():
    defaults = dict(page="Dashboard",action_done=None,last_plate=None,uploader_key=0,)
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

_init_state()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("# 🚗 Challan-AI")
st.sidebar.markdown("---")

NAV = [("Dashboard","🏠"),("Issue Challan","📸"),("Vehicle Database","🚘"),("Register Vehicle","➕"),]

for label, icon in NAV:
    if st.sidebar.button(f"{icon}  {label}",width="stretch"):
        if label == "Issue Challan":
            st.session_state.uploader_key += 1
            st.session_state.action_done = None
            st.session_state.last_plate = None
        st.session_state.page = label
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "Dashboard":
    st.title("📊 Dashboard")

    total, total_amt, pending = get_dashboard_stats()

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"#### 🚘 Total Challans \n#### {total}")
    c2.markdown(f"#### 💰 Total Amount \n##### ₹ {total_amt:,}")
    c3.markdown(f"#### ⏳ Pending \n#### {pending}")

    st.markdown("---")

    data = get_all_challans()
    if data:
        df = pd.DataFrame(data, columns=["ID","Car Number","Amount","Reason","Date","Status"])
        search = st.text_input("🔍 Search by Car Number")
        if search:
            df = df[df["Car Number"].str.contains(search.upper(), na=False)]
        st.dataframe(df,  width="stretch", height=400)
    else:
        st.info("No challans issued yet.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ISSUE CHALLAN
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Issue Challan":
    st.title("📸 Issue Challan")
    file = st.file_uploader("Upload vehicle image", type=["jpg","jpeg","png"],key=st.session_state.uploader_key)

    if file:
        # ── Decode image ──────────────────────────────────────────────────────
        img_bytes = np.frombuffer(file.read(), np.uint8)
        img_bgr   = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)

        annotated, plate_roi = detect_plate(img_bgr)

        if plate_roi is None:
            st.error("❌ No number plate detected. Please upload a clearer image.")
            st.stop()

        # ── OCR ───────────────────────────────────────────────────────────────
        car_number = read_plate(plate_roi)
        match = PLATE_RE.search(car_number)

        if not match:
            st.error(f"❌ Plate read as **{car_number}** — invalid format. Try another image.")
            st.stop()

        car_number = match.group(0)

        # reset action when plate changes
        if st.session_state.last_plate != car_number:
            st.session_state.action_done = None
            st.session_state.last_plate = car_number

        owner   = get_owner(car_number)
        pending = get_pending_amount(car_number)

        # ── Layout ────────────────────────────────────────────────────────────
        col1, col2 = st.columns([1, 1])

        with col1:
            annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            st.image(annotated_rgb,width=250)
            st.markdown(f"#### 🚗 {car_number}")
            if owner:
                st.markdown(f"- **Name:** {owner[1]}\n- **Age:** {owner[2]}\n- **Place:** {owner[3]}\n- **Mobile:** {owner[4]}")
            else:
                st.warning("⚠️ Vehicle not registered.")

        with col2:
            st.markdown("#### 🚨 Challan Details")
            reason = st.selectbox("Violation", list(FINE_MAP.keys()))
            fine   = FINE_MAP[reason]
            total  = fine + pending
            now      = datetime.now()
            date_str = now.strftime("%d-%m-%Y")
            time_str = now.strftime("%I:%M %p")

            st.write(f"💰 Fine: {fine}")
            st.write(f"📅 Datte: {date_str}")
            st.write(f"⏰ Time: {time_str}")
            st.write(f"💸 Pending: {pending}")
            st.write(f"##### Total Amount : {total}")

        # ── Action buttons ────────────────────────────────────────────────────
        if owner:
            if st.session_state.action_done is None:
                b1, b2 = st.columns(2)
                if b1.button("🚨 Issue Challan"):
                    insert_challan(car_number, fine, reason,now.strftime("%Y-%m-%d"), "Pending")
                    st.session_state.action_done = "issue"
                    st.rerun()
                if b2.button("💳 Pay Challan"):
                    insert_challan(car_number, fine, reason,now.strftime("%Y-%m-%d"), "Paid")
                    st.session_state.action_done = "pay"
                    st.rerun()
            else:
                if st.session_state.action_done == "issue":
                    st.success("✅ Challan issued — status: **Pending**")
                else:
                    st.success("✅ Challan recorded — status: **Paid**")
            
            st.markdown("---")
            
            # ── WhatsApp & PDF ────────────────────────────────────────────────
            wA, wB = st.columns(2)

            with wA:
                if st.button("📞 Send WhatsApp"):
                    mobile = owner[4]
                    if not PHONE_RE.match(mobile):
                        st.error("❌ Invalid mobile number in database.")
                    else:
                        try:
                            send_whatsapp(owner, car_number, reason,fine, pending, total, date_str, time_str)
                            st.success("✅ WhatsApp sent successfully!")
                        except Exception as e:
                            st.error(f"❌ WhatsApp failed: {e}")
            with wB:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
                    tmp_path = tf.name
                Image.fromarray(annotated_rgb).save(tmp_path)
                pdf_bytes = generate_pdf(car_number, owner, reason,fine, pending, total, date_str, time_str, tmp_path)
                os.unlink(tmp_path)
                st.download_button("📄 Download PDF", pdf_bytes,file_name=f"challan_{car_number}.pdf",mime="application/pdf")
        else:
            st.info("Register this vehicle to issue a challan.")
            if st.button("➕ Register Vehicle"):
                st.session_state.prefill_car = car_number
                st.session_state.page = "Register Vehicle"
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: REGISTER VEHICLE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Register Vehicle":
    st.title("➕ Register Vehicle")

    prefill = st.session_state.get("prefill_car", "")

    c1, c2 = st.columns(2)
    car_no   = c1.text_input("🚗 Car Number", value=prefill).upper().strip()
    name     = c1.text_input("👤 Owner Name")
    location = c2.text_input("📍 Location")
    mobile   = c2.text_input("📱 Mobile ")
    age = st.number_input("🎂 Age",18,100)

    if st.button("Register Vehicle"):
        upsert_vehicle(car_no, name, age, location, mobile)
        st.success(f"✅ Vehicle **{car_no}** registered successfully!")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: VEHICLE DATABASE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Vehicle Database":
    st.title("🚘 Vehicle Database")
    data = get_all_vehicles()
    if data:
        df = pd.DataFrame(data, columns=["Car Number","Owner Name","Age","Location","Mobile"])
        search = st.text_input("🔍 Search")
        if search:
            mask = df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)
            df = df[mask]
        st.dataframe(df,width="stretch", height=450)
        st.caption(f"{len(df)} vehicle(s) shown")
    else:
        st.warning("No vehicles registered yet.")
