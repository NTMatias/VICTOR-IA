import logging
from logging.handlers import RotatingFileHandler


def setup_logging(data_dir):
    logger = logging.getLogger("victor")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = RotatingFileHandler(data_dir / "victor.log", maxBytes=2_000_000, backupCount=4, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        logger.addHandler(handler)
    # SDK debug logging puede contener cabeceras o cuerpos privados.
    for name in ("httpx", "httpcore", "openai", "anthropic", "google_genai"):
        logging.getLogger(name).setLevel(logging.WARNING)
    return logger
