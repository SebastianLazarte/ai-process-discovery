"""Write the API contract that the Next.js client generates its types from (RS-69, ADR 0009).

A test fails when the committed file differs from the running app, so a route change
ships with its contract. The file carries a fixed `info.version` instead of the release
version, so a release bump never makes it stale; the live `/api/openapi.json` still reports
the release. Regenerate after changing a route or a schema:

    uv run python scripts/export_openapi.py
"""

import json
import sys
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.main import create_app

CONTRACT = Path(__file__).resolve().parent.parent / "frontend" / "openapi.json"
CONTRACT_VERSION = "unversioned"


def contract() -> str:
    schema: dict[str, Any] = create_app(
        Settings(database_url="sqlite://", log_level="WARNING")
    ).openapi()
    schema["info"]["version"] = CONTRACT_VERSION
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    CONTRACT.write_text(contract(), encoding="utf-8", newline="\n")
    sys.stdout.write("Wrote frontend/openapi.json\n")


if __name__ == "__main__":
    main()
