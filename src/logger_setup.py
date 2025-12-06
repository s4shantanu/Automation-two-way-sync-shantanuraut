"""Logger setup module for the automation sync project."""
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_logger(name: str):
    """Create and configure a logger with the specified name.
    
    Args:
        name: The name for the logger instance
        
    Returns:
        Configured logger instance
    """
    # Get log level from environment, default to INFO
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        force=True  # This ensures the config is applied even if logging was previously configured
    )
    return logging.getLogger(name)
