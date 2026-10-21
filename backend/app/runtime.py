import asyncio
import inspect
from collections.abc import Coroutine
from typing import Any, cast


def unwrap(value: Any) -> Any:
    if inspect.isawaitable(value):
        try:
            from pyodide.ffi import run_sync  # type: ignore[import-not-found]
        except ImportError:
            return asyncio.run(cast(Coroutine[Any, Any, Any], value))
        return run_sync(value)
    return value
