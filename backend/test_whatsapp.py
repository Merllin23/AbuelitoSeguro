import os
import httpx
from dotenv import load_dotenv

from app.services.whatsapp_service import enviar_mensaje_whatsapp

load_dotenv()

destinatario = os.getenv("WHATSAPP_TEST_NUMBER")

try:
    resultado = enviar_mensaje_whatsapp(
        destinatario,
        "Hola, este es un mensaje de prueba de AbuelitoSeguro. Tu recordatorio de medicamento está listo."
    )

    print("Mensaje enviado correctamente.")
    print(resultado)

except httpx.HTTPStatusError as error:
    print("Meta rechazó la solicitud.")
    print("Código HTTP:", error.response.status_code)
    print("Detalle del error:")
    print(error.response.text)

except Exception as error:
    print("Error:", str(error))