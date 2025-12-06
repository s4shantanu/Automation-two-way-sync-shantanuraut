"""Airtable API client for lead management."""
from typing import Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

try:
    from ..config import Config
    from ..logger_setup import get_logger
except ImportError:
    # Fallback for direct execution
    from config import Config
    from logger_setup import get_logger

logger = get_logger("airtable_client")

HEADERS = {
    "Authorization": f"Bearer {Config.AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type(Exception))
async def list_leads(filter_formula: Optional[str] = None, page_size: int = 100):
    """
    Returns list of Airtable records (raw JSON records)
    This handles simple pagination using 'offset' param.
    """
    records = []
    params = {"pageSize": page_size}
    if filter_formula:
        params["filterByFormula"] = filter_formula

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = Config.AIRTABLE_BASE_URL
        while True:
            resp = await client.get(url, headers=HEADERS, params=params)
            if resp.status_code >= 500:
                logger.warning("Airtable server error %s", resp.status_code)
                resp.raise_for_status()
            if resp.status_code != 200:
                logger.error("Airtable list_leads failed %s %s", resp.status_code, resp.text)
                resp.raise_for_status()
            data = resp.json()
            records.extend(data.get("records", []))
            offset = data.get("offset")
            if not offset:
                break
            params["offset"] = offset
    return records

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type(Exception))
async def update_lead(lead_id: str, fields: dict):
    url = f"{Config.AIRTABLE_BASE_URL}/{lead_id}"
    payload = {"fields": fields}
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.patch(url, json=payload, headers=HEADERS)
    if resp.status_code not in (200, 201):
        logger.error("Airtable update failed %s %s", resp.status_code, resp.text)
        resp.raise_for_status()
    return resp.json()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type(Exception))
async def create_lead(fields: dict):
    url = Config.AIRTABLE_BASE_URL
    payload = {"fields": fields}
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, json=payload, headers=HEADERS)
    if resp.status_code not in (200, 201):
        logger.error("Airtable create failed %s %s", resp.status_code, resp.text)
        resp.raise_for_status()
    return resp.json()
