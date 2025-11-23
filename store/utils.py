import requests

import random
import requests

# ---- OTP GENERATOR ----
def generate_otp():
    return str(random.randint(100000, 999999))

from twilio.rest import Client

def send_sms_otp(mobile, otp):
    account_sid = ""
    auth_token = ""
    twilio_number = ""

    client = Client(account_sid, auth_token)

   
    message = client.messages.create(
        body=f"Your WhatsApp OTP is {otp}",
        from_="whatsapp:+918590912155",  # Twilio sandbox number
        to=f"whatsapp:+91{mobile}"      # User mobile on WhatsApp
    )

    return message.sid
  

