"""
Main FastAPI application entry point.
Mounts static files, Jinja2 templates, and includes API routers.
"""

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from backend.app.routes import router as api_router
from backend.app.services import movie_service

app = FastAPI(
    title="CineMatch AI — Movie Recommendation System",
    description="Content-based movie recommendation system powered by NLP & Cosine Similarity over the TMDB 5000 dataset.",
    version="1.0.0"
)

# Enable CORS for local dev and API clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Mount Static Files & Templates safely for serverless environments
for d in [STATIC_DIR, os.path.join(STATIC_DIR, "css"), os.path.join(STATIC_DIR, "js"), TEMPLATES_DIR]:
    try:
        os.makedirs(d, exist_ok=True)
    except OSError:
        pass

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Include API Router
app.include_router(api_router)

@app.get("/", response_class=HTMLResponse, summary="Main Cinema Dashboard")
async def home(request: Request):
    spotlight = movie_service.get_spotlight_movie()
    genres = movie_service.get_all_genres()
    trending = movie_service.get_trending_movies(limit=12)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "spotlight": spotlight,
            "genres": genres,
            "trending": trending,
            "total_movies": len(movie_service.movies)
        }
    )

@app.get("/health", summary="Health Check")
async def health():
    return {
        "status": "healthy",
        "movies_loaded": len(movie_service.movies),
        "recommendations_loaded": len(movie_service.recommendations)
    }
