from typing import List, Optional
from pydantic import BaseModel, Field

class MovieBase(BaseModel):
    id: int
    title: str
    overview: str = ""
    genres: List[str] = Field(default_factory=list)
    cast: List[str] = Field(default_factory=list)
    director: Optional[str] = None
    release_year: Optional[int] = None
    vote_average: float = 0.0
    popularity: float = 0.0
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None

class MovieDetail(MovieBase):
    keywords: List[str] = Field(default_factory=list)

class Recommendation(BaseModel):
    id: int
    title: str
    overview: str = ""
    genres: List[str] = Field(default_factory=list)
    director: Optional[str] = None
    release_year: Optional[int] = None
    vote_average: float = 0.0
    poster_url: Optional[str] = None
    match_score: int = 95  # Percentage e.g. 96% match

class MovieSearchResponse(BaseModel):
    total: int
    page: int
    page_size: int
    results: List[MovieBase]
