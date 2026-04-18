import json
import uuid
import logging
import httpx
import time
import os
from datetime import datetime, timezone
from app.utils.dynamodb import table
from app.utils.sqs import send_message

logger = logging.getLogger(__name__)

CARD_API_URL = os.getenv("CARD_API_URL", "")
START_PAYMENT_QUEUE_URL = os.getenv("START_PAYMENT_QUEUE_URL", "")
CHECK_BALANCE_QUEUE_URL = os.getenv("CHECK_BALANCE_QUEUE_URL", "")
TRANSACTION_QUEUE_URL = os.getenv("TRANSACTION_QUEUE_URL", "")


def initiate_payment(card_id: str, service: dict):
    # Validar tarjeta con Card Service
    card = _get_card(card_id)
    if not card:
        return {"error": "Tarjeta no encontrada"}

    # Crear registro en DynamoDB
    trace_id = str(uuid.uuid4())
    item = {
        "traceId": trace_id,
        "cardId": card_id,
        "userId": card["userId"],
        "service": service,
        "status": "INITIAL",
        "timestamp": int(datetime.now(timezone.utc).timestamp()),
        "updatedAt": int(datetime.now(timezone.utc).timestamp()),
    }
    table.put_item(Item=item)
    logger.info(f"payment_service: registro creado traceId={trace_id}")

    # Encolar en SQS para iniciar flujo
    send_message(START_PAYMENT_QUEUE_URL, {"traceId": trace_id})
    return {"traceId": trace_id}


def get_payment_status(trace_id: str):
    result = table.get_item(Key={"traceId": trace_id})
    payment = result.get("Item")
    if not payment:
        return {"error": "Transaccion no encontrada"}
    return payment


# ── Lógica de Orquestación (SQS Triggers) ──────────────────────────────────

def process_start_payment(trace_id: str):
    logger.info(f"payment_service: start_payment traceId={trace_id}")
    time.sleep(5)

    # Confirmar registro inicial
    table.update_item(
        Key={"traceId": trace_id},
        UpdateExpression="SET #s = :s, updatedAt = :t",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": "INITIAL",
            ":t": int(datetime.now(timezone.utc).timestamp()),
        },
    )

    # Pasar a verificacion de saldo
    send_message(CHECK_BALANCE_QUEUE_URL, {"traceId": trace_id})


def process_check_balance(trace_id: str):
    logger.info(f"payment_service: check_balance traceId={trace_id}")
    time.sleep(5)

    payment = get_payment_status(trace_id)
    if "error" in payment:
        raise ValueError(payment["error"])

    required_amount = float(payment["service"]["Precio Mensual (US$)"])
    card_id = payment["cardId"]

    # Consultar saldo
    balance = _get_card_balance(card_id)

    if balance < required_amount:
        logger.warning(f"payment_service: saldo insuficiente traceId={trace_id}")
        _update_status(trace_id, "FAILED", "La cuenta no tiene saldo disponible")
        return

    _update_status(trace_id, "IN_PROGRESS")
    send_message(TRANSACTION_QUEUE_URL, {"traceId": trace_id})


def process_transaction(trace_id: str):
    logger.info(f"payment_service: transaction traceId={trace_id}")
    time.sleep(5)

    payment = get_payment_status(trace_id)
    if "error" in payment:
        raise ValueError(payment["error"])

    try:
        # Debito real via Card Service
        response = httpx.post(
            f"{CARD_API_URL}/transactions/purchase",
            json={
                "cardId": payment["cardId"],
                "merchant": payment["service"]["Proveedor"],
                "amount": float(payment["service"]["Precio Mensual (US$)"]),
            },
            timeout=10.0,
        )
        response.raise_for_status()

        _update_status(trace_id, "FINISH")
        logger.info(f"payment_service: transaccion exitosa traceId={trace_id}")

    except Exception as e:
        logger.error(f"payment_service: error en transaccion traceId={trace_id}: {str(e)}")
        _update_status(trace_id, "FAILED", str(e))
        raise


# ── Helpers ───────────────────────────────────────────────────────────────

def _get_card(card_id: str):
    try:
        response = httpx.get(f"{CARD_API_URL}/cards/{card_id}", timeout=10.0)
        return response.json() if response.status_code == 200 else None
    except Exception:
        return None


def _get_card_balance(card_id: str):
    response = httpx.get(f"{CARD_API_URL}/cards/{card_id}/balance", timeout=10.0)
    response.raise_for_status()
    return float(response.json()["balance"])


def _update_status(trace_id, status, error=None):
    update_expr = "SET #s = :s, updatedAt = :t"
    expr_names = {"#s": "status"}
    expr_values = {
        ":s": status,
        ":t": int(datetime.now(timezone.utc).timestamp()),
    }
    if error:
        update_expr += ", #e = :e"
        expr_names["#e"] = "error"
        expr_values[":e"] = error

    table.update_item(
        Key={"traceId": trace_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )
