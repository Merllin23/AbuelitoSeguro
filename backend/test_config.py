import os
from dotenv import load_dotenv

load_dotenv()

print("Token configurado:", bool(os.getenv("WHATSAPP_TOKEN")))
print("Phone Number ID:", os.getenv("WHATSAPP_PHONE_NUMBER_ID"))
print("Destinatario:", os.getenv("WHATSAPP_TEST_NUMBER"))
print(
    "Token de verificación:",
    bool(os.getenv("WHATSAPP_VERIFY_TOKEN"))
)