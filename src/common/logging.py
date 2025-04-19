import sys

from loguru import logger


def setup_logging(log_level: str = "INFO"):
    logger.remove()
    logger.add(sys.stdout, level=log_level, format="<green>{time}</green> <level>{message}</level>")  # pyright:ignore[reportUnusedCallResult]
    logger.add(sys.stderr, backtrace=True, diagnose=True)  # pyright:ignore[reportUnusedCallResult]  # exception hook
