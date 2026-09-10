"""
CineMatch AI — Movie Recommendation System Launcher.
Run with: python run.py
"""

import os
import sys
import uvicorn

def main():
    movies_path = os.path.join("data", "movies.json")
    recs_path = os.path.join("data", "recommendations.json")

    # If data files do not exist, run the preprocessing pipeline automatically
    if not (os.path.exists(movies_path) and os.path.exists(recs_path)):
        print("\n=======================================================")
        print("  Running Data Preparation Pipeline for First-Time Setup...")
        print("=======================================================\n")
        from backend.pipeline.prepare_data import prepare_data
        prepare_data("data")

    banner = r"""
    ===================================================================
      🎬 CineMatch AI — Intelligent Movie Recommendation System
    ===================================================================
      🌐 Frontend & App:     http://127.0.0.1:8000
      📚 Interactive API:    http://127.0.0.1:8000/docs
      ❤️ Health Check:       http://127.0.0.1:8000/health
    ===================================================================
    """
    print(banner)

    # Launch Uvicorn ASGI server
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
