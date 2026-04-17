import json
import logging
from app.services.payment_service import process_start_payment

logger = logging.getLogger()

def handler(event, context):
    for record in event["Records"]:
        try:
            body = json.loads(record["body"])
            process_start_payment(body["traceId"])
        except Exception as e:
            logger.error(f"Error start_payment: {str(e)}")
            raise
