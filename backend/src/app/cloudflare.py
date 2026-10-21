"""Conversions between Python and JavaScript values for Cloudflare bindings (D1, Workers AI).

On Cloudflare the app runs in Pyodide, where binding calls take and return JavaScript objects.
On CPython (uvicorn, pytest) there is nothing to convert, so both helpers return their input.
"""

from typing import Any

try:
    from js import Object
    from pyodide.ffi import JsProxy
    from pyodide.ffi import to_js as _to_js

    def to_js(value: Any) -> Any:
        return _to_js(value, dict_converter=Object.fromEntries)

    def to_py(value: Any) -> Any:
        return value.to_py() if isinstance(value, JsProxy) else value

except ImportError:

    def to_js(value: Any) -> Any:
        return value

    def to_py(value: Any) -> Any:
        return value
