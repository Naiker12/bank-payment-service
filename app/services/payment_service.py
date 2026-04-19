import os
import httpx
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CARD_API_URL = os.getenv("CARD_API_URL", "")

def _get_card(card_id):
    """
    Consulta los detalles de una tarjeta en el servicio de tarjetas (Legacy).
    """
    try:
        response = httpx.get(f"{CARD_API_URL}/cards/{card_id}", timeout=5.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching card {card_id}: {str(e)}")
        return None

def _extract_price(service):
    """
    Extrae el precio numérico del objeto servicio del catálogo.
    """
    try:
        price_str = service.get("Precio", service.get("precio", "0"))
        # Limpiar símbolos de moneda y convertir a float
        clean_price = "".join(c for c in str(price_str) if c.isdigit() or c == '.')
        return float(clean_price)
    except Exception as e:
        logger.error(f"Error extracting price: {str(e)}")
        return 0.0
