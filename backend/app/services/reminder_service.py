
from datetime import datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app import models
from app.services.whatsapp_service import enviar_mensaje_whatsapp


ZONA_HORARIA = ZoneInfo("America/Lima")


def enviar_recordatorio(recordatorio, adulto):
    """
    Intenta enviar el recordatorio al WhatsApp del adulto mayor.
    """

    telefono = adulto.telefono

    if not telefono:
        return False

    telefono = "".join(
        caracter for caracter in telefono
        if caracter.isdigit()
    )

    if not telefono:
        return False

    try:
        enviar_mensaje_whatsapp(
            destinatario=telefono,
            mensaje=recordatorio.mensaje
        )
        return True

    except Exception as error:
        print(
            f"Error enviando WhatsApp al adulto {adulto.id}: {error}"
        )
        return False


def generar_recordatorios_del_minuto():
    """
    Busca medicamentos cuyo horario coincide con la hora actual,
    genera el registro y trata de enviarlo por WhatsApp.
    """

    ahora = datetime.now(ZONA_HORARIA)
    hora_actual = ahora.strftime("%H:%M")

    db = SessionLocal()
    generados = 0

    try:
        medicamentos = db.query(models.Medicamento).filter(
            models.Medicamento.horario == hora_actual
        ).all()

        for medicamento in medicamentos:

            fecha_programada = datetime.combine(
                ahora.date(),
                time.fromisoformat(medicamento.horario)
            )

            existente = db.query(models.Recordatorio).filter(
                models.Recordatorio.medicamento_id == medicamento.id,
                models.Recordatorio.fecha_programada == fecha_programada
            ).first()

            if existente:
                continue

            nuevo_recordatorio = models.Recordatorio(
                mensaje=(
                    f"Hola. Este es un recordatorio de AbuelitoSeguro: "
                    f"es momento de tomar {medicamento.nombre}, "
                    f"dosis {medicamento.dosis}."
                ),
                estado="pendiente_envio",
                origen="automatico",
                fecha_programada=fecha_programada,
                adulto_id=medicamento.adulto_id,
                medicamento_id=medicamento.id
            )

            db.add(nuevo_recordatorio)

            try:
                db.commit()
                db.refresh(nuevo_recordatorio)
                generados += 1

            except IntegrityError:
                db.rollback()
                continue

            adulto = db.query(models.AdultoMayor).filter(
                models.AdultoMayor.id == medicamento.adulto_id
            ).first()

            enviado = (
                enviar_recordatorio(nuevo_recordatorio, adulto)
                if adulto else False
            )

            nuevo_recordatorio.estado = (
                "enviado" if enviado else "error"
            )

            db.commit()

        return generados

    finally:
        db.close()


def crear_recordatorio_prueba(medicamento_id: int, db):
    """
    Genera un recordatorio manual y prueba su envío por WhatsApp.
    """

    medicamento = db.query(models.Medicamento).filter(
        models.Medicamento.id == medicamento_id
    ).first()

    if not medicamento:
        return None

    ahora = datetime.now(ZONA_HORARIA).replace(
        second=0,
        microsecond=0,
        tzinfo=None
    )

    existente = db.query(models.Recordatorio).filter(
        models.Recordatorio.medicamento_id == medicamento.id,
        models.Recordatorio.fecha_programada == ahora
    ).first()

    if existente:
        return existente

    nuevo_recordatorio = models.Recordatorio(
        mensaje=(
            f"PRUEBA de AbuelitoSeguro: es momento de tomar "
            f"{medicamento.nombre}, dosis {medicamento.dosis}."
        ),
        estado="pendiente_envio",
        origen="prueba",
        fecha_programada=ahora,
        adulto_id=medicamento.adulto_id,
        medicamento_id=medicamento.id
    )

    db.add(nuevo_recordatorio)
    db.commit()
    db.refresh(nuevo_recordatorio)

    adulto = db.query(models.AdultoMayor).filter(
        models.AdultoMayor.id == medicamento.adulto_id
    ).first()

    enviado = (
        enviar_recordatorio(nuevo_recordatorio, adulto)
        if adulto else False
    )

    nuevo_recordatorio.estado = (
        "enviado" if enviado else "error"
    )

    db.commit()
    db.refresh(nuevo_recordatorio)

    return nuevo_recordatorio
