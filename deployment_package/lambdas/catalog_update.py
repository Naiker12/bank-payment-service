import json
from app.services.catalog_service import update_catalog

def handler(event, context):
    try:
        body = event.get("body", "")
        if event.get("isBase64Encoded"):
            import base64
            body = base64.b64decode(body).decode("utf-8")
        
        result = update_catalog(body)
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
