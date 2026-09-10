# Movie Recommendation System — Python-Centric Architecture & Plan

## 1. Executive Summary
This project transforms the Jupyter/Colab Content-Based Filtering model (built on the TMDB 5000 Movies & Credits dataset) into a complete, modern Full-Stack Web Application **built entirely using Python and Python-compatible technologies**.

No Node.js or npm is required. The entire application (backend API, recommendation engine, and dynamic frontend UI) is powered by Python.

---

## 2. Python Tech Stack

| Layer | Technology | Why Chosen & Compatibility |
|---|---|---|
| **Backend & Server** | **FastAPI + Uvicorn** | High-speed async Python framework. Already installed in your environment! Provides REST API and auto-generated Swagger docs (`/docs`). |
| **Frontend Rendering** | **Jinja2 Templates + Modern Vanilla Web UI** | 100% Python-driven templating (`Jinja2` already installed). Zero Node.js/npm dependencies. Enables cinema-grade streaming UI with dark glassmorphism, instant search, and modals. |
| **ML & NLP Pipeline** | **pandas**, **scikit-learn**, **nltk** (`PorterStemmer`) | The exact Python libraries from your Colab notebook for data cleaning, stemming, count vectorization, and cosine similarity. |
| **Serving & Storage** | **Precomputed Compact JSON / SQLite** | High-performance Python data structures (`orjson`/`json`) pre-indexing top-15 neighbors for sub-5ms lookup times. |
| **Poster & Backdrop Service** | **Requests / HTTPX (Python)** | Python client fetching movie posters & backdrops from TMDB API with high-quality dynamic visual fallbacks. |

> **Alternative Option — Streamlit**: If you prefer writing UI purely in Python widget scripts (`st.selectbox`, `st.button`, `st.image`), we can build a **Streamlit** application (`pip install streamlit`). However, **FastAPI + Jinja2** is strongly recommended because it delivers a true modern cinema experience (like Netflix/Letterboxd) with search autocomplete, fluid animations, and modals while remaining 100% Python-run.

---

## 3. System Architecture & Workflow

```
+-------------------------------------------------------------------------+
|                    FRONTEND (Rendered via Python Jinja2)                |
|           Modern Dark Cinema UI (Glassmorphism, Vanilla CSS, JS)         |
|                                                                         |
|  [ Hero Spotlight ]   [ Live Search / Autocomplete ]   [ Genre Filters ] |
|  [ Movie Grid / Cards ]    [ Recommendation Carousel ]  [ Detail Modal ]|
+------------------------------------+------------------------------------+
                                     |
               HTTP Requests to FastAPI (Same Python Service)
                                     |
                                     v
+-------------------------------------------------------------------------+
|                     BACKEND (FastAPI + Uvicorn)                         |
|                                                                         |
|  Endpoints:                                                             |
|   - GET  /                      (Serves Main UI via Jinja2)             |
|   - GET  /api/movies            (Paginated movie list + search/filter)  |
|   - GET  /api/movies/{id}       (Movie details + cast & crew)           |
|   - GET  /api/recommend/{id}    (Top 5-10 similar movies + match score) |
|   - GET  /api/genres            (List of available genres)              |
|   - GET  /api/trending          (Top rated / most popular movies)       |
|   - GET  /docs                  (Interactive Swagger API Docs)          |
+------------------------------------+------------------------------------+
                                     |
               Loads preprocessed data & similarity indices
                                     |
                                     v
+-------------------------------------------------------------------------+
|                         ML PIPELINE / DATA (Python)                     |
|                                                                         |
|  1. Ingest `tmdb_5000_movies.csv` & `tmdb_5000_credits.csv`            |
|  2. Clean & extract tags (genres, keywords, top-3 cast, director)      |
|  3. Stem tags with PorterStemmer (NLTK)                                 |
|  4. CountVectorizer(max_features=5000, stop_words='english')           |
|  5. Cosine Similarity Calculation                                       |
|  6. Export compact `movies.json` & `recommendations.json`               |
+-------------------------------------------------------------------------+
```

---

## 4. Project Structure (100% Python)

```
movie_recommendation_system/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app instance, static mounting, template routes
│   │   ├── routes.py            # API endpoints (/api/movies, /api/recommend, etc.)
│   │   ├── services.py          # Data lookup, recommendation engine, poster fetching
│   │   └── models.py            # Pydantic schemas for movies and recommendations
│   │
│   ├── pipeline/
│   │   ├── __init__.py
│   │   └── prepare_data.py      # Cleans TMDB 5000 data, computes similarity & exports JSON
│   │
│   ├── static/                  # Static assets served by FastAPI
│   │   ├── css/
│   │   │   └── style.css        # Cinema dark theme, glassmorphism, responsive grid
│   │   ├── js/
│   │   │   └── app.js           # Live autocomplete, recommendation triggers, modal logic
│   │   └── img/
│   │       └── placeholder.svg  # Fallback movie poster artwork
│   │
│   ├── templates/               # Jinja2 HTML templates rendered by FastAPI
│   │   ├── base.html            # Core layout with fonts & meta tags
│   │   └── index.html           # Main cinema dashboard, hero, search, grid, modal
│   │
│   └── requirements.txt         # Python dependencies
│
├── data/                        # Processed movie metadata & recommendation index
│   ├── movies.json
│   └── recommendations.json
│
├── notebook.ipynb               # Original Colab research notebook
├── run.py                       # Single Python command to start the entire app
└── plan.md                      # Architecture & implementation specification
```

---

## 5. Step-by-Step Implementation Plan

### Step 1: ML Pipeline & Data Extraction (`backend/pipeline/prepare_data.py`)
- Setup Python dependencies: `pandas`, `scikit-learn`, `nltk`, `requests`.
- Download TMDB 5000 movies and credits dataset.
- Implement data transformation mirroring the Colab notebook:
  - Extract genres, keywords, top 3 cast members, and director.
  - Normalize text and apply `PorterStemmer` from `nltk`.
  - Generate bag-of-words using `CountVectorizer(max_features=5000, stop_words='english')`.
  - Compute cosine similarity.
- Pre-calculate top 15 similar movies per movie and serialize to `data/movies.json` and `data/recommendations.json`.

### Step 2: FastAPI Backend Engine (`backend/app/`)
- Setup FastAPI server with CORS, static file hosting (`backend/static`), and Jinja2 templates (`backend/templates`).
- Implement endpoints:
  - `GET /`: Renders main UI with trending movies.
  - `GET /api/movies?q=...&genre=...`: Search movies with real-time autocomplete suggestions.
  - `GET /api/movies/{id}`: Full details (overview, genres, cast, crew, release year, rating).
  - `GET /api/recommend/{id_or_title}`: Recommendations with cosine similarity scores.
  - `GET /api/trending`: Most popular and top-rated movies.
  - `GET /api/genres`: Distinct list of genres.
- Add TMDB poster/backdrop fetching with automatic graceful fallback.

### Step 3: Cinema-Grade Frontend (`backend/templates/` & `backend/static/`)
- Design an immersive, dark streaming UI:
  - Deep obsidian palette (`#090D16`, `#111827`), glowing neon accents (electric indigo `#6366F1`, crimson `#F43F5E`), glassmorphism panels (`backdrop-filter: blur(16px)`).
  - **Hero Spotlight**: Dynamic banner showcasing featured movie with backdrop and one-click "Find Similar Movies".
  - **Live Search Bar**: Real-time autocomplete dropdown with keyboard navigation and poster thumbnails.
  - **Genre Filter Pills**: Smooth horizontal scrolling pills (Action, Sci-Fi, Drama, Thriller, etc.).
  - **Interactive Movie Cards**: Hover elevation, rating badge (`★ 8.2`), year, and "Recommend Similar" action.
  - **Recommendation Drawer / Grid**: "Because you liked [Movie Title]..." with match percentage badges (`98% Match`).
  - **Movie Detail Modal**: High-res backdrop, synopsis, director, cast chips, and related recommendations.

### Step 4: Verification & Single-Command Launcher (`run.py`)
- Create `run.py` so the user can start everything with `python run.py`.
- Automated test script verifying all API endpoints and HTML rendering.
- Manual browser verification to ensure smooth animations and instant recommendations.
