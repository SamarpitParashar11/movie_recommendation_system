"""
Business logic and data access services for the Movie Recommendation System.
Loads precomputed movies and recommendation indices for microsecond lookups.
Includes dynamic poster & backdrop resolution with fallback SVG rendering.
"""

import json
import os
import urllib.parse
from typing import Dict, List, Optional
import requests

# Curated CDN posters for TMDB top movies for instant high-def imagery
CURATED_POSTERS = {
    19995: "https://image.tmdb.org/t/p/w500/kyeqWdyUXW608qlYkRqosgbbJyK.jpg",  # Avatar
    155: "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",    # The Dark Knight
    27205: "https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg",  # Inception
    157336: "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg", # Interstellar
    557: "https://image.tmdb.org/t/p/w500/gh4c2bhLYQEZApEiymH0cuHNoe2.jpg",    # Spider-Man
    558: "https://image.tmdb.org/t/p/w500/olxpyq9MgrMl3Tvxflue7bp0ITz.jpg",    # Spider-Man 2
    559: "https://image.tmdb.org/t/p/w500/2jLxvdMSqt8rhK2m9QpB42q9P0c.jpg",    # Spider-Man 3
    24428: "https://image.tmdb.org/t/p/w500/RYMX2wcKCBAr24UyPD7xwmjaTn.jpg",  # The Avengers
    299536: "https://image.tmdb.org/t/p/w500/7WsyChQLEftFiDOVTGkv3hFpyyt.jpg", # Avengers: Infinity War
    299534: "https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg", # Avengers: Endgame
    597: "https://image.tmdb.org/t/p/w500/9xjZS2rlVxm8SFx8kPC3aIGCOYQ.jpg",    # Titanic
    1726: "https://image.tmdb.org/t/p/w500/78lPtwv72eTNqFW9COBYI0dWDJa.jpg",   # Iron Man
    680: "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg",    # Pulp Fiction
    13: "https://image.tmdb.org/t/p/w500/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg",     # Forrest Gump
    278: "https://image.tmdb.org/t/p/w500/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg",    # The Shawshank Redemption
    238: "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg",    # The Godfather
    120: "https://image.tmdb.org/t/p/w500/6oom5QYQ2yQTMJIbnvbkBL9cDK6.jpg",    # Lord of the Rings: Fellowship
    121: "https://image.tmdb.org/t/p/w500/5VTN0pR8gcqV3EPUHHfMGnJYN9L.jpg",    # Lord of the Rings: Two Towers
    122: "https://image.tmdb.org/t/p/w500/rCzpDGLbOoPwLjy3OAm5NUPOTrC.jpg",    # Lord of the Rings: Return of the King
    603: "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",    # The Matrix
    807: "https://image.tmdb.org/t/p/w500/69Sns8WoET6CfaYlIkHbla4l7nC.jpg",    # Se7en
    11: "https://image.tmdb.org/t/p/w500/6FfCtAuVAW8XJjZ7eWeLibRLWTw.jpg",     # Star Wars
    1891: "https://image.tmdb.org/t/p/w500/nNAeTmF4CMbU2Fz9Vebs83vO2hR.jpg",   # The Empire Strikes Back
    49026: "https://image.tmdb.org/t/p/w500/vzvKcPQ4o7TjWeGMcBtIY8fqGZZ.jpg",  # The Dark Knight Rises
}

CURATED_BACKDROPS = {
    19995: "https://image.tmdb.org/t/p/w1280/vL5W4R3yvpm8Zq5gZ6x0h6rWwM3.jpg",
    155: "https://image.tmdb.org/t/p/w1280/hkBaDkMWbLaf8B1r5SvR4BuZGpH.jpg",
    27205: "https://image.tmdb.org/t/p/w1280/8ZTVqvKDQ8emSGUEMjsS4yHAwrp.jpg",
    157336: "https://image.tmdb.org/t/p/w1280/xJHokMbljvjADYdit5fK5VQsXEG.jpg",
    557: "https://image.tmdb.org/t/p/w1280/sWvxBXviVvmYhT8Pvgk7f1Lz6H8.jpg",
    558: "https://image.tmdb.org/t/p/w1280/6MQ0mQGZ5WlqL2F3Q7yMvFkF5Ea.jpg",
    24428: "https://image.tmdb.org/t/p/w1280/9BBTo63ANSmhC4e6r62OJFuK2GL.jpg",
}

class MovieService:
    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            # Resolve data directory relative to repository root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.data_dir = os.path.join(base_dir, "data")
        else:
            self.data_dir = data_dir
        self.movies: List[dict] = []
        self.movies_by_id: Dict[int, dict] = {}
        self.recommendations: Dict[str, List[dict]] = {}
        self.title_to_id: Dict[str, int] = {}
        self.genres_set = set()
        self.tmdb_api_key = os.getenv("TMDB_API_KEY", "").strip()
        self.poster_cache: Dict[int, str] = {}
        self.load_data()

    def load_data(self):
        movies_path = os.path.join(self.data_dir, "movies.json")
        recs_path = os.path.join(self.data_dir, "recommendations.json")
        title_path = os.path.join(self.data_dir, "title_to_id.json")

        if not (os.path.exists(movies_path) and os.path.exists(recs_path)):
            print(f"[WARN] Data files not found in {self.data_dir}. Pipeline must be run first.")
            return

        with open(movies_path, "r", encoding="utf-8") as f:
            self.movies = json.load(f)

        with open(recs_path, "r", encoding="utf-8") as f:
            self.recommendations = json.load(f)

        if os.path.exists(title_path):
            with open(title_path, "r", encoding="utf-8") as f:
                self.title_to_id = json.load(f)
        else:
            self.title_to_id = {m["title"].lower(): m["id"] for m in self.movies}

        for m in self.movies:
            self.movies_by_id[m["id"]] = m
            for g in m.get("genres", []):
                self.genres_set.add(g)

        print(f"[INFO] MovieService loaded {len(self.movies)} movies and {len(self.recommendations)} recommendation sets.")

    def get_all_genres(self) -> List[str]:
        return sorted(list(self.genres_set))

    def get_poster_url(self, movie_id: int, title: str, genres: List[str] = None) -> str:
        # 1. Curated fast high-res CDN
        if movie_id in CURATED_POSTERS:
            return CURATED_POSTERS[movie_id]

        if movie_id in self.poster_cache:
            return self.poster_cache[movie_id]

        # 2. TMDB API live lookup if user configured a key
        if self.tmdb_api_key:
            try:
                url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={self.tmdb_api_key}"
                resp = requests.get(url, timeout=1.5)
                if resp.status_code == 200:
                    data = resp.json()
                    poster_path = data.get("poster_path")
                    if poster_path:
                        full_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                        self.poster_cache[movie_id] = full_url
                        return full_url
            except Exception:
                pass

        # 3. Dynamic Elegant Dark Poster Artwork SVG fallback (no external dependency, never breaks)
        return self._generate_fallback_poster(movie_id, title, genres)

    def get_backdrop_url(self, movie_id: int) -> str:
        if movie_id in CURATED_BACKDROPS:
            return CURATED_BACKDROPS[movie_id]
        if movie_id in CURATED_POSTERS:
            return CURATED_POSTERS[movie_id]
        return ""

    def _generate_fallback_poster(self, movie_id: int, title: str, genres: Optional[List[str]]) -> str:
        genre_label = (genres[0] if genres else "Cinema").upper()
        # Seed color hue based on id for vibrant varied palettes
        hue1 = (movie_id * 37) % 360
        hue2 = (hue1 + 45) % 360

        # Truncate title cleanly
        short_title = title if len(title) <= 24 else title[:22] + "..."
        safe_title = urllib.parse.quote(short_title)
        safe_genre = urllib.parse.quote(genre_label)

        # SVG data URI
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 450" width="300" height="450">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="hsl({hue1}, 70%, 15%)" />
      <stop offset="100%" stop-color="hsl({hue2}, 80%, 7%)" />
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="30%" r="50%">
      <stop offset="0%" stop-color="hsl({hue1}, 90%, 55%)" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="transparent" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="300" height="450" fill="url(#grad)"/>
  <circle cx="150" cy="160" r="120" fill="url(#glow)"/>
  <rect x="20" y="20" width="260" height="410" rx="16" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="1.5"/>
  <g transform="translate(150, 160)" text-anchor="middle">
    <circle r="36" fill="rgba(255,255,255,0.06)" stroke="hsl({hue1}, 80%, 65%)" stroke-width="2"/>
    <polygon points="-8,-14 16,0 -8,14" fill="hsl({hue1}, 85%, 70%)"/>
  </g>
  <rect x="30" y="270" width="70" height="20" rx="4" fill="hsl({hue1}, 70%, 25%)" stroke="hsl({hue1}, 80%, 45%)" stroke-width="1"/>
  <text x="65" y="284" fill="#E2E8F0" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="10" font-weight="700" letter-spacing="1" text-anchor="middle">{safe_genre}</text>
  <text x="30" y="325" fill="#FFFFFF" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="20" font-weight="800">
    <tspan x="30" dy="0">{safe_title}</tspan>
  </text>
  <text x="30" y="400" fill="rgba(255,255,255,0.4)" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="500">TMDB CINEMA ARCHIVE</text>
</svg>"""
        return f"data:image/svg+xml;utf8,{urllib.parse.quote(svg)}"

    def enrich_movie(self, movie: dict) -> dict:
        m = dict(movie)
        m["poster_url"] = self.get_poster_url(m["id"], m["title"], m.get("genres"))
        m["backdrop_url"] = self.get_backdrop_url(m["id"])
        return m

    def get_movie_by_id(self, movie_id: int) -> Optional[dict]:
        movie = self.movies_by_id.get(movie_id)
        if not movie:
            return None
        return self.enrich_movie(movie)

    def get_movie_by_title(self, title: str) -> Optional[dict]:
        movie_id = self.title_to_id.get(title.strip().lower())
        if movie_id:
            return self.get_movie_by_id(movie_id)

        # Partial match fallback
        t_lower = title.strip().lower()
        for m in self.movies:
            if t_lower in m["title"].lower():
                return self.enrich_movie(m)
        return None

    def get_recommendations(self, identifier: str, limit: int = 10) -> List[dict]:
        """Lookup recommendations either by numeric ID or by movie title."""
        target_id = None
        if identifier.isdigit():
            target_id = int(identifier)
        else:
            m = self.get_movie_by_title(identifier)
            if m:
                target_id = m["id"]

        if not target_id or str(target_id) not in self.recommendations:
            return []

        raw_recs = self.recommendations[str(target_id)][:limit]
        enriched = []
        for r in raw_recs:
            enriched.append({
                "id": r["id"],
                "title": r["title"],
                "overview": r["overview"],
                "genres": r["genres"],
                "director": r.get("director"),
                "release_year": r.get("release_year"),
                "vote_average": r.get("vote_average", 0.0),
                "match_score": r.get("match_score", 90),
                "poster_url": self.get_poster_url(r["id"], r["title"], r.get("genres")),
            })
        return enriched

    def search_movies(self, query: str = "", genre: str = "", page: int = 1, page_size: int = 24) -> dict:
        filtered = self.movies

        if genre:
            g_lower = genre.strip().lower()
            filtered = [m for m in filtered if any(g.lower() == g_lower for g in m.get("genres", []))]

        if query:
            q_lower = query.strip().lower()
            # Prioritize prefix match, then substring match
            starts = [m for m in filtered if m["title"].lower().startswith(q_lower)]
            contains = [m for m in filtered if q_lower in m["title"].lower() and not m["title"].lower().startswith(q_lower)]
            filtered = starts + contains

        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = filtered[start:end]

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "results": [self.enrich_movie(m) for m in paginated]
        }

    def get_trending_movies(self, limit: int = 12) -> List[dict]:
        """Returns top popular movies sorted by popularity and rating."""
        sorted_movies = sorted(
            self.movies,
            key=lambda x: (x.get("popularity", 0) * 0.7 + x.get("vote_average", 0) * 10),
            reverse=True
        )
        return [self.enrich_movie(m) for m in sorted_movies[:limit]]

    def get_spotlight_movie(self) -> Optional[dict]:
        """Returns a featured spotlight movie for the hero banner (e.g. Inception or Interstellar)."""
        spotlight_ids = [27205, 157336, 19995, 155, 24428]
        for sid in spotlight_ids:
            if sid in self.movies_by_id:
                return self.enrich_movie(self.movies_by_id[sid])
        if self.movies:
            return self.enrich_movie(self.movies[0])
        return None

# Global singleton service
movie_service = MovieService()
