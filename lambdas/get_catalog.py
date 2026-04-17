import json
from app.services.catalog_service import get_catalog

def handler(event, context):
    try:
        result = get_catalog()
        return build_response(200, result)
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
