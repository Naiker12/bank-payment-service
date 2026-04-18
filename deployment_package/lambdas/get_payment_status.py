import json
from app.services.payment_service import get_payment_status

def handler(event, context):
    try:
        trace_id = event.get("pathParameters", {}).get("traceId")
        result = get_payment_status(trace_id)
        return build_response(200 if "error" not in result else 404, result)
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
