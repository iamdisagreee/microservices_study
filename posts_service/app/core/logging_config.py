import logging
import os
from datetime import datetime, timezone
from logging.config import dictConfig
import json

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
            "message": record.getMessage()
        }

        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_record)

log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "json": {
            "()": JsonFormatter
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout"
        },
        "time_rotating_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": LOG_FILE,
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 7
        },
    },
    "loggers": {
        "app": {"handlers": ["console", "time_rotating_file"], "level": "INFO", "propagate": False}
    },
    "root": {"handlers": ["console"], "level": "INFO"}
}

dictConfig(log_config)

logger = logging.getLogger("app")


# "time_rotating_file": {
#     "class": "logging.handlers.TimedRotatingFileHandler",
#     "level": "INFO",
#     "formatter": "json",
#     "filename": LOG_FILE,
#     "when": "midnight",
#     "interval": 1,
#     "backupCount": 7,
# },
