import json
import logging
from app.services.payment_service import process_check_balance

logger = logging.getLogger()

def handler(event, context):
    for record in event["Records"]:
        try:
            body = json.loads(record["body"])
            process_check_balance(body["traceId"])
        except Exception as e:
            logger.error(f"Error check_balance: {str(e)}")
            raise
