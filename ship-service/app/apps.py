import logging
import os
import sys
import threading

from django.apps import AppConfig as DjangoAppConfig

logger = logging.getLogger(__name__)
_consumer_started = False


class AppConfig(DjangoAppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        global _consumer_started
        if _consumer_started:
            return
        if os.environ.get("ENABLE_EVENT_CONSUMER", "1") != "1":
            return
        if "runserver" not in sys.argv:
            return
        if os.environ.get("RUN_MAIN") != "true":
            return

        from .consumers import start_consumer

        thread = threading.Thread(target=start_consumer, name="ship-event-consumer", daemon=True)
        thread.start()
        _consumer_started = True
        logger.warning("EVENT_CONSUMER_THREAD_STARTED service=ship")
