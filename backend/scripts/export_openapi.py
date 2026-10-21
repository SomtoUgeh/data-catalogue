"""Prints the OpenAPI document as JSON. The frontend's `npm run gen:api` turns it into a typed client."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app.main import app  # noqa: E402

print(json.dumps(app.openapi(), indent=2))
