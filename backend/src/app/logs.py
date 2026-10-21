"""Logs one JSON object per line.

Workers Logs stores each output line as a separate entry, so a multi-line message (such as a traceback)
becomes many entries. Keeping each event on one JSON line keeps it in one entry with searchable fields.
"""

import json
import logging
import sys
import traceback
from typing import Any


def configure_logging(handler: logging.Handler | None = None) -> None:
    """Emits INFO and above as bare messages, to stdout unless a handler is given.

    Without this, Python drops INFO records. worker.py passes a handler that writes to the JS console;
    force=True lets that call replace the stdout handler set when app.main is imported.
    """
    handlers = [handler or logging.StreamHandler(sys.stdout)]
    logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=handlers, force=True)


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    logger.log(level, json.dumps({"event": event, "level": logging.getLevelName(level), **fields}, default=str))


def current_traceback() -> str:
    """The traceback of the exception being handled, as one string for a log field."""
    return traceback.format_exc()


def describe(exc: BaseException) -> str:
    """A one-line summary of an exception, for example "TimeoutError" or "ValueError: bad input"."""
    message = str(exc).strip()
    return f"{type(exc).__name__}: {message}" if message else type(exc).__name__
