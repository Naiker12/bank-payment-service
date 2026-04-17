import json
from app.services.payment_service import initiate_payment

def handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        card_id = body.get("cardId")
        service = body.get("service")
        
        result = initiate_payment(card_id, service)
        return build_response(200 if "error" not in result else 400, result)
    except Exception as e:
        return build_response(500, {"error": str(e)})

def build_response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }
