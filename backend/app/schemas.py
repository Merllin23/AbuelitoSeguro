
from pydantic import BaseModel, ConfigDict, Field, EmailStr
from datetime import datetime
from typing import Optional


# =====================================
# FAMILIARES
# =====================================

class FamiliarCreate(BaseModel):
    nombre: str
    correo: EmailStr
    telefono: str
    password: str = Field(min_length=8)


class FamiliarLogin(BaseModel):
    correo: EmailStr
    password: str


class FamiliarResponse(BaseModel):
    id: int
    nombre: str
    correo: EmailStr
    telefono: str

    model_config = ConfigDict(from_attributes=True)


# =====================================
# ADULTOS MAYORES
# =====================================

class AdultoCreate(BaseModel):
    nombre: str
    telefono: str


class AdultoResponse(AdultoCreate):
    id: int
    familiar_id: int

    model_config = ConfigDict(from_attributes=True)


# =====================================
# MEDICAMENTOS
# =====================================

class MedicamentoCreate(BaseModel):
    nombre: str
    dosis: str
    horario: str = Field(
        pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$"
    )
    adulto_id: int


class MedicamentoResponse(MedicamentoCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


# =====================================
# CONFIRMACIONES
# =====================================

class ConfirmacionCreate(BaseModel):
    mensaje: str
    estado: str
    adulto_id: int
    medicamento_id: Optional[int] = None


class ConfirmacionResponse(ConfirmacionCreate):
    id: int
    fecha: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================
# ALERTAS
# =====================================

class AlertaCreate(BaseModel):
    tipo: str
    mensaje: str
    adulto_id: int


class AlertaResponse(AlertaCreate):
    id: int
    estado: str
    fecha: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================
# RECORDATORIOS
# =====================================

class RecordatorioResponse(BaseModel):
    id: int
    mensaje: str
    estado: str
    origen: str
    fecha_programada: datetime
    fecha_creacion: datetime
    adulto_id: int
    medicamento_id: int

    model_config = ConfigDict(from_attributes=True)


# =====================================
# PROCESAMIENTO DE RESPUESTAS
# =====================================

class RespuestaProcesar(BaseModel):
    texto: str
    adulto_id: int
    medicamento_id: int | None = None
