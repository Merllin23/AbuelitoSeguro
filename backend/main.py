
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler

from app.database import Base, engine, get_db
from app import models, schemas
from app.security import (
    hash_password,
    verify_password,
    crear_access_token,
    verificar_access_token
)
from app.services.response_service import procesar_respuesta
from app.services.reminder_service import (
    generar_recordatorios_del_minuto,
    crear_recordatorio_prueba
)
from app.api.routes.whatsapp import router as whatsapp_router


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
    version="2.0.0",
    lifespan=lifespan
)

Base.metadata.create_all(bind=engine)

app.include_router(whatsapp_router)


# =====================================
# AUTENTICACIÓN
# =====================================

security = HTTPBearer()


def obtener_familiar_actual(
    credenciales: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    familiar_id = verificar_access_token(credenciales.credentials)

    if familiar_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )

    familiar = db.query(models.Familiar).filter(
        models.Familiar.id == familiar_id
    ).first()

    if not familiar:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Familiar no encontrado"
        )

    return familiar


# =====================================
# VERIFICAR PROPIEDAD DEL ADULTO
# =====================================

def verificar_adulto(
    adulto_id: int,
    familiar_id: int,
    db: Session
):
    adulto = db.query(models.AdultoMayor).filter(
        models.AdultoMayor.id == adulto_id,
        models.AdultoMayor.familiar_id == familiar_id
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
# REGISTRO DE FAMILIARES
# =====================================

@app.post(
    "/familiares/registro",
    response_model=schemas.FamiliarResponse,
    status_code=201
)
def registrar_familiar(
    familiar: schemas.FamiliarCreate,
    db: Session = Depends(get_db)
):
    correo = str(familiar.correo).lower()

    existente = db.query(models.Familiar).filter(
        models.Familiar.correo == correo
    ).first()

    if existente:
        raise HTTPException(
            status_code=409,
            detail="Este correo ya está registrado"
        )

    nuevo_familiar = models.Familiar(
        nombre=familiar.nombre,
        correo=correo,
        telefono=familiar.telefono,
        password_hash=hash_password(familiar.password)
    )

    db.add(nuevo_familiar)
    db.commit()
    db.refresh(nuevo_familiar)

    return nuevo_familiar


# =====================================
# INICIO DE SESIÓN
# =====================================

@app.post("/familiares/login")
def iniciar_sesion(
    datos: schemas.FamiliarLogin,
    db: Session = Depends(get_db)
):
    correo = str(datos.correo).lower()

    familiar = db.query(models.Familiar).filter(
        models.Familiar.correo == correo
    ).first()

    if not familiar or not verify_password(
        datos.password,
        familiar.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos"
        )

    token = crear_access_token(familiar.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "familiar": schemas.FamiliarResponse.model_validate(familiar)
    }


# =====================================
# PERFIL DEL FAMILIAR
# =====================================

@app.get(
    "/familiares/me",
    response_model=schemas.FamiliarResponse
)
def obtener_perfil(
    familiar = Depends(obtener_familiar_actual)
):
    return familiar


# =====================================
# ADULTOS MAYORES
# =====================================

@app.post(
    "/adultos/",
    response_model=schemas.AdultoResponse,
    status_code=201
)
def registrar_adulto(
    adulto: schemas.AdultoCreate,
    db: Session = Depends(get_db),
    familiar = Depends(obtener_familiar_actual)
):
    nuevo_adulto = models.AdultoMayor(
        **adulto.model_dump(),
        familiar_id=familiar.id
    )

    db.add(nuevo_adulto)
    db.commit()
    db.refresh(nuevo_adulto)

    return nuevo_adulto


@app.get(
    "/adultos/",
    response_model=list[schemas.AdultoResponse]
)
def listar_adultos(
    db: Session = Depends(get_db),
    familiar = Depends(obtener_familiar_actual)
):
    return db.query(models.AdultoMayor).filter(
        models.AdultoMayor.familiar_id == familiar.id
    ).all()


# =====================================
# MEDICAMENTOS
# =====================================

@app.post(
    "/medicamentos/",
    response_model=schemas.MedicamentoResponse
)
def registrar_medicamento(
    medicamento: schemas.MedicamentoCreate,
    db: Session = Depends(get_db),
    familiar = Depends(obtener_familiar_actual)
):
    verificar_adulto(
        medicamento.adulto_id,
        familiar.id,
        db
    )

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
    db: Session = Depends(get_db),
    familiar = Depends(obtener_familiar_actual)
):
    verificar_adulto(adulto_id, familiar.id, db)

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
    db: Session = Depends(get_db),
    familiar = Depends(obtener_familiar_actual)
):
    verificar_adulto(
        confirmacion.adulto_id,
        familiar.id,
        db
    )

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
    db: Session = Depends(get_db),
    familiar = Depends(obtener_familiar_actual)
):
    verificar_adulto(adulto_id, familiar.id, db)

    return db.query(models.Confirmacion).filter(
        models.Confirmacion.adulto_id == adulto_id
    ).all()


# =====================================
# ALERTAS
# =====================================

@app.post(
    "/alertas/",
    response_model=schemas.AlertaResponse
)
def generar_alerta(
    alerta: schemas.AlertaCreate,
    db: Session = Depends(get_db),
    familiar = Depends(obtener_familiar_actual)
):
    verificar_adulto(alerta.adulto_id, familiar.id, db)

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
    db: Session = Depends(get_db),
    familiar = Depends(obtener_familiar_actual)
):
    verificar_adulto(adulto_id, familiar.id, db)

    return db.query(models.Alerta).filter(
        models.Alerta.adulto_id == adulto_id
    ).all()


@app.patch(
    "/alertas/{alerta_id}/atender",
    response_model=schemas.AlertaResponse
)
def atender_alerta(
    alerta_id: int,
    db: Session = Depends(get_db),
    familiar = Depends(obtener_familiar_actual)
):
    alerta = db.query(models.Alerta).join(
        models.AdultoMayor
    ).filter(
        models.Alerta.id == alerta_id,
        models.AdultoMayor.familiar_id == familiar.id
    ).first()

    if not alerta:
        raise HTTPException(
            status_code=404,
            detail="Alerta no encontrada"
        )

    alerta.estado = "atendida"

    db.commit()
    db.refresh(alerta)

    return alerta

# =====================================
# RECORDATORIOS
# =====================================

@app.post(
    "/recordatorios/probar/{medicamento_id}",
    response_model=schemas.RecordatorioResponse
)
def probar_recordatorio(
    medicamento_id: int,
    db: Session = Depends(get_db),
    familiar = Depends(obtener_familiar_actual)
):
    medicamento = db.query(models.Medicamento).join(
        models.AdultoMayor
    ).filter(
        models.Medicamento.id == medicamento_id,
        models.AdultoMayor.familiar_id == familiar.id
    ).first()

    if not medicamento:
        raise HTTPException(
            status_code=404,
            detail="Medicamento no encontrado"
        )

    recordatorio = crear_recordatorio_prueba(
        medicamento_id,
        db
    )

    if not recordatorio:
        raise HTTPException(
            status_code=404,
            detail="No se pudo crear el recordatorio"
        )

    return recordatorio


@app.get(
    "/recordatorios/adulto/{adulto_id}",
    response_model=list[schemas.RecordatorioResponse]
)
def listar_recordatorios(
    adulto_id: int,
    db: Session = Depends(get_db),
    familiar = Depends(obtener_familiar_actual)
):
    verificar_adulto(adulto_id, familiar.id, db)

    return db.query(models.Recordatorio).filter(
        models.Recordatorio.adulto_id == adulto_id
    ).order_by(
        models.Recordatorio.fecha_programada.desc()
    ).all()


# =====================================
# PROCESAR RESPUESTAS
# =====================================


@app.post("/respuestas/procesar")
def procesar_respuesta_adulto(
    datos: schemas.RespuestaProcesar,
    db: Session = Depends(get_db),
    familiar = Depends(obtener_familiar_actual)
):
    try:
        verificar_adulto(
            datos.adulto_id,
            familiar.id,
            db
        )

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


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)