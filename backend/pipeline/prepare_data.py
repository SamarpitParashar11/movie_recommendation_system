"""
Data preprocessing and recommendation model pipeline for TMDB 5000 dataset.
Replicates and optimizes the logic from notebook.ipynb to produce pre-indexed
movie metadata and recommendation tables for sub-millisecond API response.
"""

import ast
import json
import os
import sys
import kagglehub
import numpy as np
import pandas as pd
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def safe_literal_eval(text):
    if pd.isna(text) or not text:
        return []
    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return []

def extract_names(text):
    data = safe_literal_eval(text)
    return [item['name'] for item in data if isinstance(item, dict) and 'name' in item]

def extract_top_cast(text, limit=3):
    data = safe_literal_eval(text)
    return [item['name'] for item in data[:limit] if isinstance(item, dict) and 'name' in item]

def extract_director(text):
    data = safe_literal_eval(text)
    for item in data:
        if isinstance(item, dict) and item.get('job') == 'Director':
            return item.get('name')
    return None

def remove_spaces(items):
    return [item.replace(" ", "") for item in items if isinstance(item, str)]

def prepare_data(output_dir="data"):
    print("[1/6] Locating TMDB 5000 dataset via kagglehub...")
    dataset_path = kagglehub.dataset_download("tmdb/tmdb-movie-metadata")
    movies_csv = os.path.join(dataset_path, "tmdb_5000_movies.csv")
    credits_csv = os.path.join(dataset_path, "tmdb_5000_credits.csv")

    print(f"[2/6] Loading CSV files from {dataset_path}...")
    movies_df = pd.read_csv(movies_csv)
    credits_df = pd.read_csv(credits_csv)

    print(f"Original movies shape: {movies_df.shape}, credits shape: {credits_df.shape}")
    merged_df = movies_df.merge(credits_df, on='title')
    print(f"Merged dataset shape: {merged_df.shape}")

    # Keep necessary columns
    cols = ['id', 'title', 'overview', 'popularity', 'genres', 'keywords', 'cast', 'crew', 'vote_average', 'release_date']
    df = merged_df[cols].copy()
    df.dropna(subset=['overview', 'title', 'id'], inplace=True)
    df.drop_duplicates(subset=['id'], inplace=True)

    print("[3/6] Parsing structured fields and metadata...")
    # Clean release year
    df['release_year'] = pd.to_datetime(df['release_date'], errors='coerce').dt.year
    df['release_year'] = df['release_year'].fillna(0).astype(int)

    # Extract genres, keywords, cast, director
    clean_genres = df['genres'].apply(extract_names)
    clean_keywords = df['keywords'].apply(extract_names)
    clean_cast = df['cast'].apply(extract_top_cast)
    directors = df['crew'].apply(extract_director)

    # Keep raw human-readable versions for display
    df['genres_list'] = clean_genres
    df['keywords_list'] = clean_keywords
    df['cast_list'] = clean_cast
    df['director'] = directors.fillna("Unknown")

    # NLP tag creation (no spaces for multi-word entities so e.g. SamWorthington is a single token)
    genres_collapsed = clean_genres.apply(remove_spaces)
    keywords_collapsed = clean_keywords.apply(remove_spaces)
    cast_collapsed = clean_cast.apply(remove_spaces)
    director_collapsed = df['director'].apply(lambda d: [d.replace(" ", "")] if d and d != "Unknown" else [])
    overview_words = df['overview'].apply(lambda x: str(x).split())

    df['tags'] = overview_words + genres_collapsed + keywords_collapsed + cast_collapsed + director_collapsed
    df['tags_str'] = df['tags'].apply(lambda words: " ".join(words).lower())

    print("[4/6] Applying PorterStemmer to tags...")
    ps = PorterStemmer()
    df['stemmed_tags'] = df['tags_str'].apply(lambda text: " ".join([ps.stem(w) for w in text.split()]))

    print("[5/6] Building CountVectorizer matrix (5000 features) & Cosine Similarity...")
    cv = CountVectorizer(max_features=5000, stop_words='english')
    vectors = cv.fit_transform(df['stemmed_tags']).toarray()
    print(f"Vectors shape: {vectors.shape}")

    similarity = cosine_similarity(vectors)
    print(f"Similarity matrix shape: {similarity.shape}")

    os.makedirs(output_dir, exist_ok=True)

    print("[6/6] Generating and exporting precomputed JSON files...")
    movies_list = []
    recommendations_map = {}
    title_to_id_map = {}

    df_reset = df.reset_index(drop=True)

    for idx, row in df_reset.iterrows():
        m_id = int(row['id'])
        m_title = str(row['title'])
        title_to_id_map[m_title.lower()] = m_id

        movie_dict = {
            "id": m_id,
            "title": m_title,
            "overview": str(row['overview']),
            "genres": row['genres_list'],
            "keywords": row['keywords_list'],
            "cast": row['cast_list'],
            "director": str(row['director']),
            "release_year": int(row['release_year']) if row['release_year'] > 0 else None,
            "vote_average": round(float(row['vote_average']), 1),
            "popularity": round(float(row['popularity']), 2),
            "poster_url": None,  # Will be populated dynamically or via TMDB
            "backdrop_url": None
        }
        movies_list.append(movie_dict)

        # Compute top 15 recommendations for this movie
        # Distances: sorted by similarity descending, skipping index 0 (self)
        distances = sorted(list(enumerate(similarity[idx])), reverse=True, key=lambda x: x[1])
        top_recs = []
        for i in distances[1:16]:
            rec_row = df_reset.iloc[i[0]]
            sim_score = float(i[1])
            # Scale similarity score to intuitive match percentage between 70% and 99%
            match_pct = max(70, min(99, int(sim_score * 100))) if sim_score > 0 else 70
            top_recs.append({
                "id": int(rec_row['id']),
                "title": str(rec_row['title']),
                "overview": str(rec_row['overview']),
                "genres": rec_row['genres_list'],
                "director": str(rec_row['director']),
                "release_year": int(rec_row['release_year']) if rec_row['release_year'] > 0 else None,
                "vote_average": round(float(rec_row['vote_average']), 1),
                "match_score": match_pct
            })
        recommendations_map[str(m_id)] = top_recs

    movies_path = os.path.join(output_dir, "movies.json")
    recs_path = os.path.join(output_dir, "recommendations.json")
    title_path = os.path.join(output_dir, "title_to_id.json")

    with open(movies_path, "w", encoding="utf-8") as f:
        json.dump(movies_list, f, indent=2)

    with open(recs_path, "w", encoding="utf-8") as f:
        json.dump(recommendations_map, f, indent=2)

    with open(title_path, "w", encoding="utf-8") as f:
        json.dump(title_to_id_map, f, indent=2)

    print(f"DONE! Processed {len(movies_list)} movies.")
    print(f"Saved: {movies_path} ({os.path.getsize(movies_path):,} bytes)")
    print(f"Saved: {recs_path} ({os.path.getsize(recs_path):,} bytes)")

if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    prepare_data(out_dir)
