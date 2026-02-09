"""
Logging configuration.
Spec reference: BACKEND_STRUCTURE.md Section 8.1
"""

import logging
import sys
from pathlib import Path


def setup_logging():
    """Configure console and file logging."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / "app.log")
    ]
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=handlers
    )
