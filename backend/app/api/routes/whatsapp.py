
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import (
    APIRouter,
    Depends,
    Query,
    HTTPException,
    Body
)
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.database import get_db
from app import models
from app.services.response_service import procesar_respuesta
from app.services.whatsapp_service import enviar_mensaje_whatsapp


load_dotenv()

router = APIRouter(
    prefix="/whatsapp",
    tags=["WhatsApp"]
)

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
ZONA_HORARIA = ZoneInfo("America/Lima")


def normalizar_telefono(telefono: str) -> str:
    return "".join(
        caracter for caracter in telefono
        if caracter.isdigit()
    )


def obtener_recordatorio_pendiente(db: Session, adulto_id: int):
    ahora = datetime.now(ZONA_HORARIA).replace(tzinfo=None)

    inicio_dia = ahora.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    return db.query(models.Recordatorio).filter(
        models.Recordatorio.adulto_id == adulto_id,
        models.Recordatorio.estado == "enviado",
        models.Recordatorio.fecha_programada >= inicio_dia,
        models.Recordatorio.fecha_programada <= ahora
    ).order_by(
        models.Recordatorio.fecha_programada.desc()
    ).first()


def notificar_familiar(adulto, resultado):
    familiar = adulto.familiar

    if not familiar or not familiar.telefono:
        print(
            f"El adulto {adulto.id} no tiene familiar registrado."
        )
        return

    telefono_familiar = normalizar_telefono(
        familiar.telefono
    )

    if not telefono_familiar:
        print(
            f"El familiar del adulto {adulto.id} no tiene "
            f"un teléfono válido."
        )
        return

    categoria = resultado.get("categoria")

    if categoria == "posible_alerta":
        mensaje = (
            f"AVISO DE ABUELITOSEGURO\n\n"
            f"El adulto mayor {adulto.nombre} ha indicado que se siente mal.\n"
            f"Mensaje recibido: {resultado.get('mensaje')}\n\n"
            f"Se recomienda comunicarse con él para verificar su estado."
        )

    elif categoria == "alerta_prioritaria":
        mensaje = (
            f"ALERTA PRIORITARIA - ABUELITOSEGURO\n\n"
            f"El adulto mayor {adulto.nombre} ha solicitado ayuda.\n"
            f"Mensaje recibido: {resultado.get('mensaje')}\n\n"
            f"Por favor, comuníquese con él lo antes posible."
        )

    else:
        return

    try:
        respuesta = enviar_mensaje_whatsapp(
            destinatario=telefono_familiar,
            mensaje=mensaje
        )

        print(
            f"Notificación enviada al familiar de {adulto.nombre}: "
            f"{respuesta}"
        )

    except Exception as error:
        print(
            f"No se pudo notificar al familiar "
            f"{telefono_familiar}: {error}"
        )


@router.get("/webhook")
def verificar_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    if (
        hub_mode == "subscribe"
        and VERIFY_TOKEN
        and hub_verify_token == VERIFY_TOKEN
    ):
        return PlainTextResponse(
            content=hub_challenge or "",
            status_code=200
        )

    raise HTTPException(
        status_code=403,
        detail="Token de verificación incorrecto"
    )


@router.post("/webhook")
async def recibir_mensaje_whatsapp(
    datos: dict = Body(...),
    db: Session = Depends(get_db)
):
    try:
        entradas = datos.get("entry", [])

        for entrada in entradas:
            cambios = entrada.get("changes", [])

            for cambio in cambios:
                valor = cambio.get("value", {})
                mensajes = valor.get("messages", [])

                for mensaje in mensajes:

                    if mensaje.get("type") != "text":
                        continue

                    telefono = mensaje.get("from")
                    texto = mensaje.get("text", {}).get("body", "")

                    if not telefono or not texto:
                        continue

                    telefono = normalizar_telefono(telefono)

                    adultos = db.query(
                        models.AdultoMayor
                    ).all()

                    adulto = next(
                        (
                            persona for persona in adultos
                            if normalizar_telefono(persona.telefono)
                            == telefono
                        ),
                        None
                    )

                    if not adulto:
                        print(f"Remitente no registrado: {telefono}")
                        continue

                    recordatorio = obtener_recordatorio_pendiente(
                        db,
                        adulto.id
                    )

                    medicamento_id = (
                        recordatorio.medicamento_id
                        if recordatorio else None
                    )

                    resultado = procesar_respuesta(
                        texto=texto,
                        adulto_id=adulto.id,
                        medicamento_id=medicamento_id,
                        db=db
                    )

                    if (
                        recordatorio
                        and resultado["categoria"] in [
                            "confirmacion",
                            "pendiente"
                        ]
                    ):
                        recordatorio.estado = "respuesta_recibida"
                        db.commit()

                    print(
                        f"Respuesta procesada del adulto {adulto.id}: "
                        f"{resultado}"
                    )

                    print(
                        f"Medicamento asociado: {medicamento_id}"
                    )

                    if resultado["categoria"] in [
                        "posible_alerta",
                        "alerta_prioritaria"
                    ]:
                        notificar_familiar(adulto, resultado)

        return {"estado": "recibido"}

    except Exception as error:
        db.rollback()

        print(f"Error procesando webhook: {error}")

        raise HTTPException(
            status_code=500,
            detail="Error al procesar el mensaje"
        )
