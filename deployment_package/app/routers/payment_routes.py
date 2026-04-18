from fastapi import APIRouter
from app.models.payment_model import PaymentRequest
from app.services.payment_service import initiate_payment, get_payment_status

router = APIRouter()


@router.post("/")
def pay(request: PaymentRequest):
    return initiate_payment(request.cardId, request.service)


@router.get("/status/{trace_id}")
def status(trace_id: str):
    return get_payment_status(trace_id)
