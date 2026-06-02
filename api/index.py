import sys
import os

# Add backend dir to sys.path so its local imports (agents, database, etc.) resolve
_backend = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, _backend)

from main import app  # noqa: E402 — path must be set first
