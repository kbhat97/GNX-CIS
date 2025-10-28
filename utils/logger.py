import logging
from datetime import datetime
import os

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"logs/agent_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()  # Also log to console
    ]
)

def log(message: str, level: str = "info"):
    """Log message with specified level"""
    logger = logging.getLogger("LinkedInAgent")
    getattr(logger, level.lower())(message)

def log_agent_action(agent_name: str, action: str, details: str = ""):
    """Log agent-specific actions"""
    log(f"[{agent_name}] {action}: {details}")

def log_error(error: Exception, context: str = ""):
    """Log errors with context"""
    log(f"ERROR in {context}: {str(error)}", "error")