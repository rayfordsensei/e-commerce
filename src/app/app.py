from loguru import logger

from app.create_app import create_app
from app.settings import settings

if settings.DEBUG:
    logger.info("[app] Running in debug mode")  # A placeholder...


app = create_app()
