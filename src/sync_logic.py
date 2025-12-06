"""Sync logic for two-way synchronization between Airtable and Trello."""
import asyncio
from typing import Optional

try:
    from .clients.airtable_client import list_leads, update_lead
    from .clients.trello_client import find_card_by_lead_id, create_card, update_card, list_board_cards
    from .config import Config
    from .logger_setup import get_logger
except ImportError:
    # Fallback for direct execution
    from clients.airtable_client import list_leads, update_lead
    from clients.trello_client import find_card_by_lead_id, create_card, update_card, list_board_cards
    from config import Config
    from logger_setup import get_logger

logger = get_logger("sync_logic")

# Status mapping
LEAD_TO_TRELLO_LIST = {
    "NEW": Config.TRELLO_LIST_TODO_ID,
    "CONTACTED": Config.TRELLO_LIST_IN_PROGRESS_ID,
    "QUALIFIED": Config.TRELLO_LIST_DONE_ID,
    # LOST: we'll keep card and add 'Lost' note
    "LOST": Config.TRELLO_LIST_DONE_ID
}

TRELLO_LIST_TO_LEAD = {
    Config.TRELLO_LIST_TODO_ID: "NEW",
    Config.TRELLO_LIST_IN_PROGRESS_ID: "CONTACTED",
    Config.TRELLO_LIST_DONE_ID: "QUALIFIED"
}

def build_desc_for_lead(lead_record: dict):
    rec_id = lead_record.get("id")
    fields = lead_record.get("fields", {})
    email = fields.get("Email") or fields.get("email", "")
    source = fields.get("Source") or fields.get("source", "")
    desc = f"lead_id:{rec_id}\nemail:{email}\nsource:{source}"
    return desc

async def ensure_task_for_lead(lead_record: dict):
    """
    Ensure a Trello card exists and matches desired state for a given lead.
    Idempotent: searches by lead_id tag in card description.
    """
    lead_id = lead_record.get("id")
    fields = lead_record.get("fields", {})
    name = fields.get("Name") or fields.get("name") or f"Lead {lead_id}"
    status = fields.get("Status") or fields.get("status") or "NEW"
    desired_list = LEAD_TO_TRELLO_LIST.get(status, Config.TRELLO_LIST_TODO_ID)
    desc = build_desc_for_lead(lead_record)

    try:
        card = await find_card_by_lead_id(lead_id)
    except Exception as e:
        logger.exception("Error finding card for lead %s: %s", lead_id, str(e))
        return

    try:
        if card:
            # If list or name differs update it
            card_id = card.get("id")
            updates = {}
            if card.get("idList") != desired_list:
                updates["idList"] = desired_list
            if card.get("name") != name:
                updates["name"] = name
            # always ensure description contains up-to-date fields (idempotent)
            if desc not in (card.get("desc") or ""):
                updates["desc"] = desc
            if updates:
                logger.info("Updating card %s for lead %s with %s", card_id, lead_id, updates)
                await update_card(card_id, **updates)
            else:
                logger.debug("Card %s up-to-date for lead %s", card.get("id"), lead_id)
        else:
            # Create new card with lead_id in description
            logger.info("Creating card for lead %s", lead_id)
            await create_card(list_id=desired_list, name=name, desc=desc)
    except Exception as e:
        logger.exception("Error ensuring task for lead %s: %s", lead_id, str(e))

async def sync_leads_to_tasks(filter_formula: Optional[str] = None):
    """
    Reads leads and ensures tasks exist/updated in Trello.
    """
    try:
        leads = await list_leads(filter_formula=filter_formula)
    except Exception as e:
        logger.exception("Failed to list leads: %s", str(e))
        return {"status":"error", "error": str(e)}

    tasks = [ensure_task_for_lead(lead) for lead in leads]
    await asyncio.gather(*tasks)
    return {"status":"ok", "processed": len(leads)}

# Reverse: update leads from Trello changes (poll Trello)
# For simplicity, we read every card on the board and update Airtable status if mapping differs.

async def update_leads_from_tasks():
    try:
        cards = await list_board_cards()
    except Exception as e:
        logger.exception("Failed to list trello cards: %s", str(e))
        return {"status":"error", "error": str(e)}

    processed = 0
    for card in cards:
        desc = card.get("desc") or ""
        # find lead_id token
        lead_id = None
        for line in desc.splitlines():
            if line.startswith("lead_id:"):
                lead_id = line.split("lead_id:")[1].strip()
                break
        if not lead_id:
            # Not linked to a lead — skip
            continue
        desired_lead_status = TRELLO_LIST_TO_LEAD.get(card.get("idList"), "CONTACTED")
        # Fetching lead and updating could be done by reading the record directly; here we attempt an update
        # We should avoid redundant updates: to check current value, we need the lead record fields (not shown here)
        # For simplicity, we will attempt update and Airtable will ignore no-op if field same.
        try:
            await update_lead(lead_id, {"Status": desired_lead_status})
            processed += 1
            logger.info("Updated lead %s -> status %s", lead_id, desired_lead_status)
        except Exception as e:
            logger.exception("Failed to update lead %s: %s", lead_id, str(e))
    return {"status":"ok", "processed": processed}

async def run_full_sync():
    # 1. sync leads -> tasks
    r1 = await sync_leads_to_tasks()
    # 2. sync tasks -> leads
    r2 = await update_leads_from_tasks()
    return {"leads_to_tasks": r1, "tasks_to_leads": r2}
