
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.response_service import procesar_respuesta
from app.api.routes.whatsapp import router as whatsapp_router

from app.database import Base, engine, get_db
from app import models, schemas
from app.services.reminder_service import (
    generar_recordatorios_del_minuto,
    crear_recordatorio_prueba
)


# =====================================
# PROGRAMADOR AUTOMÁTICO
# =====================================

scheduler = BackgroundScheduler(timezone="America/Lima")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(
        generar_recordatorios_del_minuto,
        trigger="interval",
        minutes=1,
        id="generar_recordatorios",
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )

    scheduler.start()

    yield

    scheduler.shutdown(wait=False)


# =====================================
# CONFIGURACIÓN DE FASTAPI
# =====================================

app = FastAPI(
    title="AbuelitoSeguro",
    description="Sistema de acompañamiento y alertas para adultos mayores",
    version="1.0.0",
    lifespan=lifespan
)


# Crear las tablas de la base de datos
Base.metadata.create_all(bind=engine)

app.include_router(whatsapp_router)


# =====================================
# FUNCIÓN AUXILIAR
# =====================================

def verificar_adulto(adulto_id: int, db: Session):
    adulto = db.query(models.AdultoMayor).filter(
        models.AdultoMayor.id == adulto_id
    ).first()

    if not adulto:
        raise HTTPException(
            status_code=404,
            detail="Adulto mayor no encontrado"
        )

    return adulto


# =====================================
# INICIO Y ESTADO
# =====================================

@app.get("/")
def inicio():
    return {
        "mensaje": "Bienvenido a AbuelitoSeguro",
        "estado": "Backend funcionando"
    }


@app.get("/health")
def verificar_estado():
    return {"status": "ok"}


# =====================================
# ADULTOS MAYORES
# =====================================

@app.post("/adultos/", response_model=schemas.AdultoResponse)
def registrar_adulto(
    adulto: schemas.AdultoCreate,
    db: Session = Depends(get_db)
):
    nuevo_adulto = models.AdultoMayor(**adulto.model_dump())

    db.add(nuevo_adulto)
    db.commit()
    db.refresh(nuevo_adulto)

    return nuevo_adulto


@app.get("/adultos/", response_model=list[schemas.AdultoResponse])
def listar_adultos(db: Session = Depends(get_db)):
    return db.query(models.AdultoMayor).all()


# =====================================
# MEDICAMENTOS
# =====================================

@app.post("/medicamentos/", response_model=schemas.MedicamentoResponse)
def registrar_medicamento(
    medicamento: schemas.MedicamentoCreate,
    db: Session = Depends(get_db)
):
    verificar_adulto(medicamento.adulto_id, db)

    nuevo_medicamento = models.Medicamento(
        **medicamento.model_dump()
    )

    db.add(nuevo_medicamento)
    db.commit()
    db.refresh(nuevo_medicamento)

    return nuevo_medicamento


@app.get(
    "/medicamentos/adulto/{adulto_id}",
    response_model=list[schemas.MedicamentoResponse]
)
def listar_medicamentos(
    adulto_id: int,
    db: Session = Depends(get_db)
):
    verificar_adulto(adulto_id, db)

    return db.query(models.Medicamento).filter(
        models.Medicamento.adulto_id == adulto_id
    ).all()


# =====================================
# CONFIRMACIONES
# =====================================

@app.post(
    "/confirmaciones/",
    response_model=schemas.ConfirmacionResponse
)
def registrar_confirmacion(
    confirmacion: schemas.ConfirmacionCreate,
    db: Session = Depends(get_db)
):
    verificar_adulto(confirmacion.adulto_id, db)

    if confirmacion.medicamento_id is not None:
        medicamento = db.query(models.Medicamento).filter(
            models.Medicamento.id == confirmacion.medicamento_id,
            models.Medicamento.adulto_id == confirmacion.adulto_id
        ).first()

        if not medicamento:
            raise HTTPException(
                status_code=404,
                detail="Medicamento no encontrado para este adulto mayor"
            )

    nueva_confirmacion = models.Confirmacion(
        **confirmacion.model_dump()
    )

    db.add(nueva_confirmacion)
    db.commit()
    db.refresh(nueva_confirmacion)

    return nueva_confirmacion


@app.get(
    "/confirmaciones/adulto/{adulto_id}",
    response_model=list[schemas.ConfirmacionResponse]
)
def listar_confirmaciones(
    adulto_id: int,
    db: Session = Depends(get_db)
):
    verificar_adulto(adulto_id, db)

    return db.query(models.Confirmacion).filter(
        models.Confirmacion.adulto_id == adulto_id
    ).all()


# =====================================
# ALERTAS
# =====================================

@app.post("/alertas/", response_model=schemas.AlertaResponse)
def generar_alerta(
    alerta: schemas.AlertaCreate,
    db: Session = Depends(get_db)
):
    verificar_adulto(alerta.adulto_id, db)

    nueva_alerta = models.Alerta(**alerta.model_dump())

    db.add(nueva_alerta)
    db.commit()
    db.refresh(nueva_alerta)

    return nueva_alerta


@app.get(
    "/alertas/adulto/{adulto_id}",
    response_model=list[schemas.AlertaResponse]
)
def listar_alertas(
    adulto_id: int,
    db: Session = Depends(get_db)
):
    verificar_adulto(adulto_id, db)

    return db.query(models.Alerta).filter(
        models.Alerta.adulto_id == adulto_id
    ).all()


# =====================================
# RECORDATORIOS
# =====================================

@app.post(
    "/recordatorios/probar/{medicamento_id}",
    response_model=schemas.RecordatorioResponse
)
def probar_recordatorio(
    medicamento_id: int,
    db: Session = Depends(get_db)
):
    recordatorio = crear_recordatorio_prueba(
        medicamento_id,
        db
    )

    if not recordatorio:
        raise HTTPException(
            status_code=404,
            detail="Medicamento no encontrado"
        )

    return recordatorio


@app.get(
    "/recordatorios/adulto/{adulto_id}",
    response_model=list[schemas.RecordatorioResponse]
)
def listar_recordatorios(
    adulto_id: int,
    db: Session = Depends(get_db)
):
    verificar_adulto(adulto_id, db)

    return db.query(models.Recordatorio).filter(
        models.Recordatorio.adulto_id == adulto_id
    ).order_by(
        models.Recordatorio.fecha_programada.desc()
    ).all()


@app.post("/respuestas/procesar")
def procesar_respuesta_adulto(
    datos: schemas.RespuestaProcesar,
    db: Session = Depends(get_db)
):
    try:
        resultado = procesar_respuesta(
            texto=datos.texto,
            adulto_id=datos.adulto_id,
            medicamento_id=datos.medicamento_id,
            db=db
        )

        return resultado

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )