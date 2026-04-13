import pywhatkit as kit
import os

def send_msg(owner, car_number, reason, fine, total_pending, grand_total, date, time):
    phone = owner[4]  
    if not phone.startswith("+91"):
        phone = "+91" + phone

    msg = f"""🚨 *Traffic Challan Notice*\n\n 🚗 Vehicle: {car_number}\n\n 👤 Owner Details \n\t Name: {owner[1]} \n\t Age: {owner[2]} \n\t Place: {owner[3]} \n\t Mobile: {phone} \n\n ⚠️ Violation: {reason} \n\n 💰 Current Fine: Rs. {fine} \n📋 Previous Pending: Rs. {total_pending} \n 🧾 Total Amount: Rs. {grand_total} \n\n 📅 Date: {date} \n\n ⏰ Time: {time} \n\n Please pay the fine promptly."""
    kit.sendwhatmsg_instantly(phone, msg)

     # ❌ REMOVE PyWhatKit default file
    if os.path.exists("PyWhatKit_DB.txt"):
        os.remove("PyWhatKit_DB.txt")