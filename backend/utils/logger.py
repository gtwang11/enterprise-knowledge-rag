"""日志配置"""

import logging
import os
from logging.handlers import RotatingFileHandler

from config import LOG_DIR


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    # Clear stale handlers (critical for uvicorn reload)
    logger.handlers.clear()

    logger.setLevel(logging.DEBUG)

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(console)

    # File handler
    log_path = os.path.join(LOG_DIR, "app.log")
    file_handler = RotatingFileHandler(
        log_path, maxBytes=10 * 1024 * 1024, backupCount=90, encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    ))
    logger.addHandler(file_handler)

    return logger


app_logger = setup_logger("eknowledge")
