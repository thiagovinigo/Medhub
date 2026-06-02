import sys
import os

# Add the project root to the path so `backend` package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.index import app
