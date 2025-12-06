import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
    AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
    AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Leads")

    TRELLO_KEY = os.getenv("TRELLO_KEY")
    TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
    TRELLO_BOARD_ID = os.getenv("TRELLO_BOARD_ID")
    TRELLO_LIST_TODO_ID = os.getenv("TRELLO_LIST_TODO_ID")
    TRELLO_LIST_IN_PROGRESS_ID = os.getenv("TRELLO_LIST_IN_PROGRESS_ID")
    TRELLO_LIST_DONE_ID = os.getenv("TRELLO_LIST_DONE_ID")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Derived
    AIRTABLE_BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
