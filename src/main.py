"""Main entry point for the automation sync application."""
import asyncio

try:
    from .logger_setup import get_logger
    from .sync_logic import run_full_sync
except ImportError:
    # Fallback for direct execution
    from logger_setup import get_logger
    from sync_logic import run_full_sync

logger = get_logger("main")

if __name__ == "__main__":
    logger.info("Starting full sync (manual trigger)")
    result = asyncio.run(run_full_sync())
    logger.info("Sync result: %s", result)
    print(result)
