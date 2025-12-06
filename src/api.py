"""FastAPI application for Airtable-Trello two-way sync."""
import asyncio

from fastapi import FastAPI, BackgroundTasks

try:
    from .logger_setup import get_logger
    from .sync_logic import run_full_sync
except ImportError:
    # Fallback for direct execution
    from logger_setup import get_logger
    from sync_logic import run_full_sync

logger = get_logger("api")
app = FastAPI(title="Airtable-Trello Two-way Sync")

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/trigger")
async def trigger(background: BackgroundTasks):
    """Trigger a manual sync operation in the background."""

    # Background function must be sync for FastAPI 0.95.2
    def _bg():
        try:
            logger.info("Manual trigger started")
            asyncio.run(run_full_sync())
            logger.info("Manual trigger finished")
        except (RuntimeError, ValueError, ConnectionError) as e:
            logger.exception("Manual trigger error: %s", str(e))
        except Exception as e:
            logger.exception("Unexpected error during manual trigger: %s", str(e))

    background.add_task(_bg)
    return {"status": "triggered"}
