import json
import uuid
import logging
import httpx
import time
import os
from decimal import Decimal
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
    now_ts = int(datetime.now(timezone.utc).timestamp())
    item = {
        "traceId": trace_id,
        "cardId": card_id,
        "userId": card.get("userId", card.get("user_id", "")),
        "service": service,
        "status": "INITIAL",
        "timestamp": now_ts,
        "updatedAt": now_ts,
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

    # Convertir Decimal a float/int para serialización JSON
    return _decimal_safe(payment)


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

    payment = _get_raw_payment(trace_id)
    if not payment:
        raise ValueError("Transaccion no encontrada")

    # Obtener precio del servicio — compatible con formato CSV
    service = payment.get("service", {})
    required_amount = _extract_price(service)
    card_id = payment["cardId"]

    # Consultar saldo desde la info de la tarjeta
    card = _get_card(card_id)
    if not card:
        _update_status(trace_id, "FAILED", "No se pudo obtener información de la tarjeta")
        return

    balance = float(card.get("balance", 0))

    if balance < required_amount:
        logger.warning(f"payment_service: saldo insuficiente traceId={trace_id}")
        _update_status(trace_id, "FAILED", "La cuenta no tiene saldo disponible")
        return

    _update_status(trace_id, "IN_PROGRESS")
    send_message(TRANSACTION_QUEUE_URL, {"traceId": trace_id})


def process_transaction(trace_id: str):
    logger.info(f"payment_service: transaction traceId={trace_id}")
    time.sleep(5)

    payment = _get_raw_payment(trace_id)
    if not payment:
        raise ValueError("Transaccion no encontrada")

    try:
        service = payment.get("service", {})
        amount = _extract_price(service)
        merchant = service.get("Proveedor", service.get("proveedor", "Desconocido"))

        # Debito real via Card Service — POST /transactions/purchase
        response = httpx.post(
            f"{CARD_API_URL}/transactions/purchase",
            json={
                "cardId": payment["cardId"],
                "merchant": merchant,
                "amount": amount,
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
    """Obtiene info de una tarjeta desde el Card Service.
    Endpoint real: GET /card/info/{card_id}
    """
    try:
        response = httpx.get(f"{CARD_API_URL}/card/info/{card_id}", timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            # El response puede venir con body como string (API Gateway proxy)
            if isinstance(data.get("body"), str):
                return json.loads(data["body"])
            return data
        return None
    except Exception as e:
        logger.error(f"payment_service: error al obtener tarjeta {card_id}: {str(e)}")
        return None


def _extract_price(service: dict) -> float:
    """Extrae el precio del servicio. Compatible con formato CSV y camelCase."""
    # Formato CSV: "Precio Mensual (US$)"
    if "Precio Mensual (US$)" in service:
        return float(service["Precio Mensual (US$)"])
    # Formato camelCase/snake_case
    if "PrecioMensual" in service:
        return float(service["PrecioMensual"])
    if "precio_mensual" in service:
        return float(service["precio_mensual"])
    raise ValueError("No se encontró el campo de precio en el servicio")


def _get_raw_payment(trace_id: str):
    """Obtiene el pago directamente de DynamoDB sin conversión."""
    result = table.get_item(Key={"traceId": trace_id})
    return result.get("Item")


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


def _decimal_safe(obj):
    """Convierte Decimal de DynamoDB a tipos serializables por JSON."""
    if isinstance(obj, dict):
        return {k: _decimal_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_decimal_safe(i) for i in obj]
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    return obj
