import json
import logging
from app.services.payment_service import process_transaction

logger = logging.getLogger()

def handler(event, context):
    for record in event["Records"]:
        try:
            body = json.loads(record["body"])
            process_transaction(body["traceId"])
        except Exception as e:
            logger.error(f"Error transaction: {str(e)}")
            raise
