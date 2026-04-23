import os
import json
import logging
from urllib import error, request

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CARD_API_URL = os.getenv("CARD_API_URL", "")

def _get_card(card_id):
    """
    Consulta los detalles de una tarjeta en el servicio de tarjetas.
    """
    candidate_paths = [
        f"/card/info/{card_id}",
        f"/cards/{card_id}",
    ]

    last_error = None
    for path in candidate_paths:
        try:
            req = request.Request(f"{CARD_API_URL}{path}", method="GET")
            with request.urlopen(req, timeout=5.0) as response:
                payload = response.read().decode("utf-8")
                return json.loads(payload)
        except error.HTTPError as exc:
            last_error = exc
            if exc.code == 404:
                continue
        except Exception as exc:
            last_error = exc

    logger.error(f"Error fetching card {card_id}: {str(last_error)}")
    return None

def _extract_price(service):
    """
    Extrae el precio numérico del objeto servicio del catálogo.
    Soporta formatos PascalCase (API) y camelCase (Frontend Normalizado).
    """
    try:
        # Intentar con múltiples posibles llaves (normalizadas y originales)
        price_str = service.get("precio_mensual", 
                    service.get("Precio", 
                    service.get("precio", "0")))
        
        # Limpiar símbolos de moneda y convertir a float
        clean_price = "".join(c for c in str(price_str) if c.isdigit() or c == '.')
        return float(clean_price) if clean_price else 0.0
    except Exception as e:
        logger.error(f"Error extracting price from {service}: {str(e)}")
        return 0.0
