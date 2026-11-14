import logging

from app.core.config import settings


def get_logger(name: str | None = None) -> logging.Logger:
    logger = logging.getLogger(name or settings.logger_name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
