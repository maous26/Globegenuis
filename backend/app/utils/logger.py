import logging
import sys
from pathlib import Path
from loguru import logger

# Remove default logger
logger.remove()

# Add custom logger
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Add file logger
log_path = Path("logs")
log_path.mkdir(exist_ok=True)

logger.add(
    log_path / "globegenius.log",
    rotation="1 day",
    retention="7 days",
    level="DEBUG"
)