"""Trello API client for card management."""
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

logger = get_logger("trello_client")

BASE = "https://api.trello.com/1"

def auth_params():
    return {"key": Config.TRELLO_KEY, "token": Config.TRELLO_TOKEN}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type(Exception))
async def list_board_cards(board_id: Optional[str] = None):
    board = board_id or Config.TRELLO_BOARD_ID
    url = f"{BASE}/boards/{board}/cards"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, params=auth_params())
    if resp.status_code != 200:
        logger.error("Trello list cards failed %s %s", resp.status_code, resp.text)
        resp.raise_for_status()
    return resp.json()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type(Exception))
async def create_card(list_id: str, name: str, desc: str = ""):
    url = f"{BASE}/cards"
    params = {**auth_params(), "idList": list_id, "name": name, "desc": desc}
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, params=params)
    if resp.status_code not in (200, 201):
        logger.error("Trello create_card failed %s %s", resp.status_code, resp.text)
        resp.raise_for_status()
    return resp.json()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type(Exception))
async def update_card(card_id: str, **kwargs):
    url = f"{BASE}/cards/{card_id}"
    params = {**auth_params(), **kwargs}
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.put(url, params=params)
    if resp.status_code not in (200, 201):
        logger.error("Trello update_card failed %s %s", resp.status_code, resp.text)
        resp.raise_for_status()
    return resp.json()

async def find_card_by_lead_id(lead_id: str):
    cards = await list_board_cards()
    for card in cards:
        desc = card.get("desc") or ""
        if f"lead_id:{lead_id}" in desc:
            return card
    return None
