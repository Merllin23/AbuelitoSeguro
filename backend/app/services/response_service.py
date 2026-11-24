
import unicodedata
from sqlalchemy.orm import Session

from app import models


def normalizar_texto(texto: str) -> str:
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        caracter for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    return texto


def procesar_respuesta(
    texto: str,
    adulto_id: int,
    medicamento_id: int | None,
    db: Session
):
    mensaje = normalizar_texto(texto)

    adulto = db.query(models.AdultoMayor).filter(
        models.AdultoMayor.id == adulto_id
    ).first()

    if not adulto:
        raise ValueError("El adulto mayor no existe.")

    if medicamento_id is not None:
        medicamento = db.query(models.Medicamento).filter(
            models.Medicamento.id == medicamento_id,
            models.Medicamento.adulto_id == adulto_id
        ).first()

        if not medicamento:
            raise ValueError(
                "El medicamento no existe o no pertenece al adulto mayor."
            )

    # 1. Solicitud de ayuda
    if (
        "necesito ayuda" in mensaje
        or "ayuda urgente" in mensaje
    ):
        alerta = models.Alerta(
            tipo="prioritaria",
            mensaje=texto,
            estado="pendiente",
            adulto_id=adulto_id
        )

        db.add(alerta)
        db.commit()
        db.refresh(alerta)

        return {
            "categoria": "alerta_prioritaria",
            "mensaje": "Se registró una alerta prioritaria.",
            "registro_id": alerta.id
        }

    # 2. Posible malestar
    negaciones = [
        "no me siento mal",
        "no me duele",
        "no tengo dolor"
    ]

    expresiones_malestar = [
        "me siento mal",
        "me duele",
        "tengo dolor"
    ]

    if (
        any(frase in mensaje for frase in expresiones_malestar)
        and not any(frase in mensaje for frase in negaciones)
    ):
        alerta = models.Alerta(
            tipo="posible_malestar",
            mensaje=texto,
            estado="pendiente",
            adulto_id=adulto_id
        )

        db.add(alerta)
        db.commit()
        db.refresh(alerta)

        return {
            "categoria": "posible_alerta",
            "mensaje": "Se registró un posible malestar.",
            "registro_id": alerta.id
        }

    # 3. Confirmación de medicamento
    respuestas_confirmadas = [
        "ya lo tome",
        "ya tome",
        "ya me lo tome",
        "ya lo he tomado",
        "ya tome mi medicamento",
        "si, ya",
        "correcto"
    ]

    if any(frase in mensaje for frase in respuestas_confirmadas):
        confirmacion = models.Confirmacion(
            mensaje=texto,
            estado="confirmado",
            adulto_id=adulto_id,
            medicamento_id=medicamento_id
        )

        db.add(confirmacion)
        db.commit()
        db.refresh(confirmacion)

        return {
            "categoria": "confirmacion",
            "mensaje": "Se registró la respuesta como confirmación.",
            "registro_id": confirmacion.id
        }

    # 4. Medicamento pendiente
    respuestas_pendientes = [
        "todavia no",
        "todavia no lo tome",
        "todavia no lo he tomado",
        "aun no",
        "aun no lo tome",
        "aun no lo he tomado",
        "no lo tome",
        "no lo he tomado"
    ]

    if (
        any(frase in mensaje for frase in respuestas_pendientes)
        or mensaje == "no"
    ):
        confirmacion = models.Confirmacion(
            mensaje=texto,
            estado="pendiente",
            adulto_id=adulto_id,
            medicamento_id=medicamento_id
        )

        db.add(confirmacion)
        db.commit()
        db.refresh(confirmacion)

        return {
            "categoria": "pendiente",
            "mensaje": "Se registró que el medicamento aún está pendiente.",
            "registro_id": confirmacion.id
        }

    # 5. Respuesta no reconocida
    confirmacion = models.Confirmacion(
        mensaje=texto,
        estado="sin_clasificar",
        adulto_id=adulto_id,
        medicamento_id=medicamento_id
    )

    db.add(confirmacion)
    db.commit()
    db.refresh(confirmacion)

    return {
        "categoria": "sin_clasificar",
        "mensaje": "La respuesta se guardó, pero no pudo clasificarse.",
        "registro_id": confirmacion.id
    }
