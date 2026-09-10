# CineMatch AI — Movie Recommendation System

A full-stack Content-Based Movie Recommendation System built **100% in Python** over the TMDB 5000 Movies & Credits dataset. 

No Node.js or npm required. The entire stack (machine learning pipeline, FastAPI backend, and cinema-grade dark streaming frontend) is powered by Python.

---

## Features
- **Machine Learning Recommendation Engine**: Content-based filtering using NLP word stemming (`PorterStemmer`), `CountVectorizer(max_features=5000)`, and `cosine_similarity`.
- **Precomputed Sub-Millisecond Lookups**: Pre-calculated nearest neighbors stored in compact indices so recommendations return in `< 5ms`.
- **Modern Streaming UI**: Deep obsidian theme (`#070A12`), glassmorphism cards, ambient glow lights, and fluid animations.
- **Hero Spotlight Banner**: Showcases featured movies with rating badges, director, cast, and one-click "Recommend Similar Movies".
- **Live Search & Autocomplete**: Real-time debounced title search with poster thumbnails and keyboard navigation (`Ctrl+K`, Arrow keys, Enter).
- **Genre Filter Pills**: Filter across 20 genres (Sci-Fi, Action, Drama, Thriller, etc.).
- **Movie Detail Modals**: High-resolution backdrops, synopsis, director, cast chips, and TMDB links.
- **Automatic Fallback Artwork**: Sleek SVG poster generator ensuring cards never show broken images.
- **Interactive Swagger API Docs**: Explore all endpoints at `/docs`.

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Run the Application
```bash
python run.py
```

Then open your browser:
- **Web App**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## Run Verification Tests
```bash
python test_app.py
```

---

## Deploy to Vercel

The project is fully configured for serverless deployment on [Vercel](https://vercel.com) via `api/index.py` and `vercel.json`.

### Option A: Deploy via GitHub (Recommended)
1. Push your project to your GitHub repository:
   ```bash
   git add .
   git commit -m "Configure Vercel serverless deployment"
   git push origin main
   ```
2. Go to your [Vercel Dashboard](https://vercel.com/dashboard) and click **Add New... > Project**.
3. Import your GitHub repository (`movie_recommendation_system`).
4. (Optional) In **Environment Variables**, add:
   - `TMDB_API_KEY`: *(Optional)* Your TMDB API v3 key if you want live dynamic poster lookups for movies outside the curated set.
5. Click **Deploy**. Vercel will automatically detect Python, install dependencies, and publish your live URL.

### Option B: Deploy via Vercel CLI
1. Log in to Vercel:
   ```bash
   npx vercel login
   ```
2. Deploy to a preview environment:
   ```bash
   npx vercel
   ```
3. Deploy to production:
   ```bash
   npx vercel --prod
   ```

---

## Project Structure
```
movie_recommendation_system/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app instance, static mounting, template routes
│   │   ├── routes.py            # REST API endpoints (/api/movies, /api/recommend, etc.)
│   │   ├── services.py          # Data queries, recommendation lookup, poster generator
│   │   └── models.py            # Pydantic data schemas
│   ├── pipeline/
│   │   └── prepare_data.py      # Cleans TMDB 5000 dataset, computes cosine similarity
│   ├── static/
│   │   ├── css/style.css        # Cinema dark theme & glassmorphism
│   │   ├── js/app.js            # Live search, recommendation triggers, modal logic
│   │   └── img/placeholder.svg  # Fallback movie poster artwork
│   ├── templates/
│   │   ├── base.html            # Layout, Google Fonts, navbar, search bar
│   │   └── index.html           # Main dashboard, hero banner, cards grid, modal
│   └── requirements.txt         # Python dependencies
├── data/
│   ├── movies.json              # Cleaned movie metadata (4,800 records)
│   ├── recommendations.json     # Precomputed similarity indices (42MB)
│   └── title_to_id.json         # Title lookup index
├── notebook.ipynb               # Original Colab research notebook
├── run.py                       # Single-command application launcher
├── test_app.py                  # Automated test suite
└── plan.md                      # Technical architecture & implementation plan
```
