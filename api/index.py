import sys
import os
import traceback

# Add the project root to the path so `backend` package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try importing FastAPI first (minimal)
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# Try to import backend and capture any error
import_error = None
try:
    from backend.main import app as real_app
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
