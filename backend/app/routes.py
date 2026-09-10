"""
FastAPI REST API routes for Movie Recommendations, Search, and Details.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.app.services import movie_service
from backend.app.models import MovieBase, MovieDetail, Recommendation, MovieSearchResponse

router = APIRouter(prefix="/api", tags=["Movies & Recommendations"])

@router.get("/genres", response_model=List[str], summary="Get list of all movie genres")
def get_genres():
    return movie_service.get_all_genres()

@router.get("/trending", response_model=List[MovieBase], summary="Get popular trending movies")
def get_trending(limit: int = Query(12, ge=1, le=50)):
    return movie_service.get_trending_movies(limit=limit)

@router.get("/movies", response_model=MovieSearchResponse, summary="Search and filter movies")
def search_movies(
    q: str = Query("", description="Movie title search query"),
    genre: str = Query("", description="Filter by genre"),
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100)
):
    return movie_service.search_movies(query=q, genre=genre, page=page, page_size=page_size)

@router.get("/autocomplete", summary="Fast live autocomplete for search bar")
def autocomplete(q: str = Query(..., min_length=1)):
    res = movie_service.search_movies(query=q, page=1, page_size=8)
    return [
        {
            "id": m["id"],
            "title": m["title"],
            "release_year": m.get("release_year"),
            "vote_average": m.get("vote_average"),
            "genres": m.get("genres", [])[:2],
            "poster_url": m.get("poster_url")
        }
        for m in res["results"]
    ]

@router.get("/movies/{movie_id}", response_model=MovieDetail, summary="Get full movie details")
def get_movie_details(movie_id: int):
    movie = movie_service.get_movie_by_id(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie with id {movie_id} not found")
    return movie

@router.get("/recommend/{identifier}", response_model=List[Recommendation], summary="Get recommendations for a movie")
def get_recommendations(
    identifier: str,
    limit: int = Query(10, ge=1, le=20)
):
    recs = movie_service.get_recommendations(identifier=identifier, limit=limit)
    if not recs:
        # Check if the movie even exists
        movie = movie_service.get_movie_by_id(int(identifier)) if identifier.isdigit() else movie_service.get_movie_by_title(identifier)
        if not movie:
            raise HTTPException(status_code=404, detail=f"Movie '{identifier}' not found in dataset")
        # Return empty if movie exists but has no neighbors
        return []
    return recs
