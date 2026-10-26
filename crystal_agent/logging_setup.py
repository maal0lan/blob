import logging
from logging.handlers import RotatingFileHandler
from .config import APP_DIR

def configure_logging(level: str = "DEBUG") -> logging.Logger:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("crystal")
    logger.setLevel(getattr(logging, level.upper(), logging.DEBUG))
    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
        file_handler = RotatingFileHandler(APP_DIR / "crystal.log", maxBytes=2_000_000, backupCount=4, encoding="utf-8")
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
        stream = logging.StreamHandler()
        stream.setFormatter(fmt)
        logger.addHandler(stream)
    return logger
