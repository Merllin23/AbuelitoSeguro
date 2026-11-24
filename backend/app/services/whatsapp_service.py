import os
import httpx
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v26.0")


def enviar_mensaje_whatsapp(destinatario: str, mensaje: str):
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        raise ValueError("Faltan las credenciales de WhatsApp.")

    url = (
        f"https://graph.facebook.com/"
        f"{API_VERSION}/{PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    datos = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": destinatario,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": mensaje
        }
    }

    respuesta = httpx.post(
        url,
        headers=headers,
        json=datos,
        timeout=20
    )

    if respuesta.status_code >= 400:
        print("Error detallado de Meta:")
        print(respuesta.text)
        respuesta.raise_for_status()

    return respuesta.json()