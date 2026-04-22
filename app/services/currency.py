import httpx
import logging

logger = logging.getLogger(__name__)

async def get_mxn_rate() -> float:
    """
    Obtiene el tipo de cambio actual de USD a MXN desde Frankfurter API.
    Retorna un valor estático de fallback (18.50) en caso de caída del servicio o falta de internet.
    """
    url = "https://api.frankfurter.dev/v1/latest?from=USD&to=MXN"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            return float(data["rates"]["MXN"])
    except Exception as e:
        logger.warning(f"No se pudo consultar Frankfurter API. Usando fallback MXN = 18.50. Error: {str(e)}")
        return 18.50
