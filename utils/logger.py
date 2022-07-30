import logging
import sys
from pathlib import Path

logger = logging.getLogger()


def setup_logger():
    Path("../logs").mkdir(exist_ok=True)
    global logger
    logger = logging.getLogger("application")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(levelname)-8s %(message)s"))
    logger.addHandler(handler)
    handler = logging.FileHandler("logs.txt")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)-8s %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)


def get_logger():
    return logger
