import json
import logging
import sys
from contextvars import ContextVar

from app.core.config import get_settings


# middleware/request_id.py sets 
request_id_var = ContextVar("request_id", default="-")

# The layout of one log line in normal (readable) mode.
TEXT_FORMAT = "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"


NOISY_LOGGERS = ["LiteLLM", "litellm", "httpx", "httpcore"]


class RequestIdFilter(logging.Filter):
    """Attaches the current request id to every log record."""

    def filter(self, record):
        record.request_id = request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """Prints each log line as one JSON object. Used when LOG_JSON=true."""

    def format(self, record):
        data = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "request_id": record.request_id,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data)


def setup_logging():
    """Call this once when the app starts (in main.py)."""
    settings = get_settings()

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())

    if settings.log_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(TEXT_FORMAT))

    root_logger = logging.getLogger()
    root_logger.handlers.clear()   # remove old handlers so lines are not printed twice
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level.upper())

    for name in NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)