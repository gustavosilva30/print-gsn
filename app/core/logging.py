from __future__ import annotations

import logging
from pathlib import Path

from loguru import logger


def configure_logging(base_dir: Path) -> None:
    log_path = base_dir / "logs" / "gsn-print-service.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.getLogger().handlers.clear()
    logger.remove()
    logger.add(log_path, rotation="10 MB", retention="30 days", level="DEBUG")
    logger.add(lambda message: print(message, end=""), level="INFO")
