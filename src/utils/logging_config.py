"""Project-wide logging setup.

Call ``configure_logging()`` once near an entry point (e.g. the pipeline runner), then use
``get_logger(__name__)`` anywhere else. Keeping this in one place gives every module a
consistent log format without each one calling ``logging.basicConfig`` itself.
"""

from __future__ import annotations

import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging once. Safe to call multiple times (later calls are no-ops)."""
    global _configured
    if _configured:
        return
    logging.basicConfig(level=level, format=LOG_FORMAT, datefmt=DATE_FORMAT, stream=sys.stdout)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger, ensuring logging has been configured first."""
    configure_logging()
    return logging.getLogger(name)
