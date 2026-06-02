import sys
import os
import traceback

_backend = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, _backend)

from fastapi import FastAPI
from fastapi.responses import JSONResponse

_import_error: str | None = None
app = FastAPI()

try:
    from main import app as _real_app  # type: ignore[assignment]
    app = _real_app
except Exception:
    _import_error = traceback.format_exc()


@app.get("/api/health")
def health():
    if _import_error:
        return JSONResponse(status_code=500, content={"ok": False, "error": _import_error})
    return {"ok": True}
