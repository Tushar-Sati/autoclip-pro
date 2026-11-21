import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("  🚀 Starting AutoClip Pro Backend (FastAPI + Worker)")
    print("  🌐 API running at: http://localhost:8000")
    print("  📑 Docs at: http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=False)
