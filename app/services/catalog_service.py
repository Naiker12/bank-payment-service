import csv
import io
import json
import logging
from app.utils.s3 import upload_csv
from app.utils.redis_client import get_redis

logger = logging.getLogger(__name__)


def update_catalog(csv_content: str):
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = [row for row in reader]

    if not rows:
        return {"error": "CSV vacio o invalido"}

    upload_csv(csv_content)

    client = get_redis()
    pipe = client.pipeline()
    pipe.delete("catalog")
    for row in rows:
        pipe.hset("catalog", row["ID"], json.dumps(row))
    pipe.execute()

    logger.info(f"catalog_service: {len(rows)} servicios sincronizados")
    return {"message": "Catalogo actualizado", "total": len(rows)}


def get_catalog():
    client = get_redis()
    raw = client.hgetall("catalog")
    if not raw:
        return []
    return [json.loads(value) for value in raw.values()]
