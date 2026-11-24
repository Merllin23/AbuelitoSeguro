
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



class AdultoMayor(Base):
    __tablename__ = "adultos_mayores"

    __table_args__ = (
        UniqueConstraint(
            "telefono",
            name="uq_adulto_telefono"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    telefono = Column(String(20), nullable=False)
    familiar_nombre = Column(String(100), nullable=False)
    familiar_telefono = Column(String(20), nullable=False)

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

    __table_args__ = (
        UniqueConstraint(
            "adulto_id",
            "nombre",
            "dosis",
            "horario",
            name="uq_medicamento_adulto"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    dosis = Column(String(100), nullable=False)
    horario = Column(String(10), nullable=False)

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
    fecha = Column(DateTime, default=datetime.now, nullable=False)

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
    tipo = Column(String(50), nullable=False)
    mensaje = Column(Text, nullable=False)
    estado = Column(String(50), default="pendiente", nullable=False)
    fecha = Column(DateTime, default=datetime.now, nullable=False)

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
            name="uq_recordatorio_medicamento_fecha"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    mensaje = Column(Text, nullable=False)
    estado = Column(String(30), default="simulado", nullable=False)
    origen = Column(String(20), default="automatico", nullable=False)

    fecha_programada = Column(DateTime, nullable=False)
    fecha_creacion = Column(
        DateTime,
        default=datetime.now,
        nullable=False
    )

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
