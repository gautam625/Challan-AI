import os
from twilio.rest import Client

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN")
FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")

if not ACCOUNT_SID:
    raise Exception("❌ TWILIO_ACCOUNT_SID not set in environment")
if not AUTH_TOKEN:
    raise Exception("❌ TWILIO_AUTH_TOKEN not set in environment")
if not FROM_NUMBER:
    raise Exception("❌ TWILIO_FROM_NUMBER not set in environment")


def send_msg(owner, car_number, reason, fine, total_pending, grand_total, date, time):
    phone = owner[4]
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
