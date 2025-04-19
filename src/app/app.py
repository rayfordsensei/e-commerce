import logging

from app.create_app import create_app
from app.settings import settings

logger = logging.getLogger("app." + __name__)

if settings.DEBUG:
    logger.info("[app] Running in debug mode")  # A placeholder...


app = create_app()
