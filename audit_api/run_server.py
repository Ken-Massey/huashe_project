"""PyCharm-friendly server entry point; run this file directly."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))


if __name__ == "__main__":
    uvicorn.run(
        "audit_api.main:app",
        host=os.getenv("AUDIT_API_HOST", "127.0.0.1"),
        port=int(os.getenv("AUDIT_API_PORT", "8000")),
        reload=False,
    )
