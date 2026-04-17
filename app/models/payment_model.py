from pydantic import BaseModel
from typing import Optional


class ServiceItem(BaseModel):
    ID: str
    Categoria: str
    Proveedor: str
    Servicio: str
    Plan: str
    PrecioMensual: float
    VelocidadDetalles: str
    Estado: str


class PaymentRequest(BaseModel):
    cardId: str
    service: dict


class PaymentResponse(BaseModel):
    traceId: str


class PaymentStatus(BaseModel):
    traceId: str
    cardId: str
    userId: str
    service: dict
    status: str
    timestamp: int
    updatedAt: int
    error: Optional[str] = None
