import json
import logging
import os
from app.services.payment_service import (
    process_start_payment,
    process_check_balance,
    process_transaction
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    for record in event.get("Records", []):
        try:
            body = json.loads(record["body"])
            trace_id = body.get("traceId")
            
            if not trace_id:
                logger.error("No traceId found in message body")
                continue
            
            event_source_arn = record.get("eventSourceARN", "")
            
            # Identificar qué paso del flujo ejecutar basándonos en el nombre de la cola
            if "start-payment" in event_source_arn:
                process_start_payment(trace_id)
            elif "check-balance" in event_source_arn:
                process_check_balance(trace_id)
            elif "transaction" in event_source_arn:
                process_transaction(trace_id)
            else:
                logger.warning(f"Origen de evento desconocido: {event_source_arn}")
                
        except Exception as e:
            logger.error(f"Error procesando registro de {record.get('eventSourceARN')}: {str(e)}")
            # Re-lanzar para que SQS reintente según la política
            raise e
