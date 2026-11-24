
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Familiar(Base):
    __tablename__ = "familiares"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(150), unique=True, index=True, nullable=False)
    telefono = Column(String(20), nullable=False)
    password_hash = Column(String(255), nullable=False)

    adultos = relationship(
        "AdultoMayor",
        back_populates="familiar"
    )


class AdultoMayor(Base):
    __tablename__ = "adultos_mayores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    telefono = Column(String(20), nullable=False)

    familiar_id = Column(
        Integer,
        ForeignKey("familiares.id"),
        nullable=False
    )

    familiar = relationship(
        "Familiar",
        back_populates="adultos"
    )

    medicamentos = relationship(
        "Medicamento",
        back_populates="adulto"
    )

    confirmaciones = relationship(
        "Confirmacion",
        back_populates="adulto"
    )

    alertas = relationship(
        "Alerta",
        back_populates="adulto"
    )

    recordatorios = relationship(
        "Recordatorio",
        back_populates="adulto"
    )


class Medicamento(Base):
    __tablename__ = "medicamentos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    dosis = Column(String(100), nullable=False)
    horario = Column(String(5), nullable=False)

    adulto_id = Column(
        Integer,
        ForeignKey("adultos_mayores.id"),
        nullable=False
    )

    adulto = relationship(
        "AdultoMayor",
        back_populates="medicamentos"
    )

    confirmaciones = relationship(
        "Confirmacion",
        back_populates="medicamento"
    )

    recordatorios = relationship(
        "Recordatorio",
        back_populates="medicamento"
    )


class Confirmacion(Base):
    __tablename__ = "confirmaciones"

    id = Column(Integer, primary_key=True, index=True)
    mensaje = Column(Text, nullable=False)
    estado = Column(String(50), nullable=False)
    fecha = Column(DateTime, default=datetime.now)

    adulto_id = Column(
        Integer,
        ForeignKey("adultos_mayores.id"),
        nullable=False
    )

    medicamento_id = Column(
        Integer,
        ForeignKey("medicamentos.id"),
        nullable=True
    )

    adulto = relationship(
        "AdultoMayor",
        back_populates="confirmaciones"
    )

    medicamento = relationship(
        "Medicamento",
        back_populates="confirmaciones"
    )


class Alerta(Base):
    __tablename__ = "alertas"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(100), nullable=False)
    mensaje = Column(Text, nullable=False)
    estado = Column(String(50), default="pendiente")
    fecha = Column(DateTime, default=datetime.now)

    adulto_id = Column(
        Integer,
        ForeignKey("adultos_mayores.id"),
        nullable=False
    )

    adulto = relationship(
        "AdultoMayor",
        back_populates="alertas"
    )


class Recordatorio(Base):
    __tablename__ = "recordatorios"

    __table_args__ = (
        UniqueConstraint(
            "medicamento_id",
            "fecha_programada",
            name="uq_medicamento_fecha"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    mensaje = Column(Text, nullable=False)
    estado = Column(String(50), default="simulado")
    origen = Column(String(50), default="automatico")
    fecha_programada = Column(DateTime, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.now)

    adulto_id = Column(
        Integer,
        ForeignKey("adultos_mayores.id"),
        nullable=False
    )

    medicamento_id = Column(
        Integer,
        ForeignKey("medicamentos.id"),
        nullable=False
    )

    adulto = relationship(
        "AdultoMayor",
        back_populates="recordatorios"
    )

    medicamento = relationship(
        "Medicamento",
        back_populates="recordatorios"
    )
