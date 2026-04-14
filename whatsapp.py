from twilio.rest import Client
import os

# ---- Twilio Credentials (set these in Render Environment Variables) ----
ACCOUNT_SID = os.environ.get("ACf8d92c36466b7768e5f00499136fa0ee")
AUTH_TOKEN   = os.environ.get("9fae8c2046b5a89f03c7087da7d0c2be")
FROM_NUMBER  = os.environ.get("whatsapp:+919004420925")  



def send_msg(owner, car_number, reason, fine, total_pending, grand_total, date, time):
    phone = owner[4]

    # Add country code if missing
    if not phone.startswith("+"):
        phone = "+91" + phone

    msg = (
        f"🚨 *Traffic Challan Notice*\n\n"
        f"🚗 Vehicle: {car_number}\n\n"
        f"👤 Owner Details\n"
        f"   Name  : {owner[1]}\n"
        f"   Age   : {owner[2]}\n"
        f"   Place : {owner[3]}\n"
        f"   Mobile: {phone}\n\n"
        f"⚠️ Violation      : {reason}\n"
        f"💰 Current Fine   : Rs. {fine}\n"
        f"📋 Prev. Pending  : Rs. {total_pending}\n"
        f"🧾 Total Amount   : Rs. {grand_total}\n\n"
        f"📅 Date : {date}\n"
        f"⏰ Time : {time}\n\n"
        f"Please pay the fine promptly to avoid further penalties."
    )

    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    message = client.messages.create(
        from_=FROM_NUMBER,             
        to=f"whatsapp:{phone}",       
        body=msg
    )

    return message.sid