
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional


# =====================================
# ADULTOS MAYORES
# =====================================

class AdultoCreate(BaseModel):
    nombre: str
    telefono: str
    familiar_nombre: str
    familiar_telefono: str


class AdultoResponse(AdultoCreate):
    id: int

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


class RespuestaProcesar(BaseModel):
    texto: str
    adulto_id: int
    medicamento_id: int | None = None