import sys
import os
import traceback

# Add both the project root AND the backend directory to sys.path
# Root: so `backend` package is importable as `backend.xxx`
# Backend dir: so backend's local imports (agents, database, etc.) work
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_backend = os.path.join(_root, "backend")
sys.path.insert(0, _root)
sys.path.insert(0, _backend)

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

import_error = None
try:
    from main import app as real_app
    app = real_app
except Exception as e:
    import_error = traceback.format_exc()

@app.get("/api/health")
def health():
    if import_error:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": import_error}
        )
    return {"status": "ok"}
