"""
Automated end-to-end verification script for CineMatch AI backend and frontend.
Tests endpoints using Starlette TestClient (runs in-memory without background server needed).
"""

import sys
from starlette.testclient import TestClient
from backend.app.main import app

def run_tests():
    print("\n>>> Initializing TestClient...")
    client = TestClient(app)

    # 1. Health check
    print(">>> Testing /health...")
    resp = client.get("/health")
    assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["movies_loaded"] >= 4000
    print(f"    PASSED! {data['movies_loaded']} movies loaded.")

    # 2. Main HTML Frontend Route
    print(">>> Testing / (HTML Frontend)...")
    resp = client.get("/")
    assert resp.status_code == 200, f"Frontend route failed: {resp.status_code}"
    assert "CineMatch" in resp.text
    assert "SPOTLIGHT FEATURE" in resp.text
    print("    PASSED! Main frontend template rendered.")

    # 3. Genres API
    print(">>> Testing /api/genres...")
    resp = client.get("/api/genres")
    assert resp.status_code == 200
    genres = resp.json()
    assert len(genres) > 10
    assert "Action" in genres and "Drama" in genres
    print(f"    PASSED! Found {len(genres)} genres.")

    # 4. Trending Movies API
    print(">>> Testing /api/trending...")
    resp = client.get("/api/trending?limit=8")
    assert resp.status_code == 200
    trending = resp.json()
    assert len(trending) == 8
    print(f"    PASSED! Top trending: {[m['title'] for m in trending[:3]]}")

    # 5. Search API
    print(">>> Testing /api/movies?q=spider-man...")
    resp = client.get("/api/movies?q=spider-man")
    assert resp.status_code == 200
    search_res = resp.json()
    assert search_res["total"] > 0
    spider_titles = [m["title"] for m in search_res["results"]]
    print(f"    PASSED! Found {search_res['total']} titles: {spider_titles[:3]}")

    # 6. Autocomplete API
    print(">>> Testing /api/autocomplete?q=incep...")
    resp = client.get("/api/autocomplete?q=incep")
    assert resp.status_code == 200
    auto_res = resp.json()
    assert any("Inception" in m["title"] for m in auto_res)
    print(f"    PASSED! Autocomplete match: {auto_res[0]['title']}")

    # 7. Movie Details API
    print(">>> Testing /api/movies/155 (The Dark Knight)...")
    resp = client.get("/api/movies/155")
    assert resp.status_code == 200
    movie = resp.json()
    assert "Dark Knight" in movie["title"]
    assert movie["director"] == "Christopher Nolan"
    print(f"    PASSED! Details: {movie['title']} directed by {movie['director']}")

    # 8. Recommendation API (Spider-Man 2)
    print(">>> Testing /api/recommend/Spider-Man%202...")
    resp = client.get("/api/recommend/Spider-Man%202")
    assert resp.status_code == 200
    recs = resp.json()
    assert len(recs) > 0
    rec_titles = [r["title"] for r in recs]
    print(f"    PASSED! Recommendations for Spider-Man 2: {rec_titles[:5]}")
    # Verify Spider-Man 3 or Spider-Man is among the top recommendations
    assert any("Spider-Man" in t for t in rec_titles), "Expected Spider-Man franchise match in recommendations"

    print("\n=======================================================")
    print("  ALL TESTS PASSED SUCCESSFULLY! (8/8 Test Suites OK)  ")
    print("=======================================================\n")

if __name__ == "__main__":
    run_tests()
