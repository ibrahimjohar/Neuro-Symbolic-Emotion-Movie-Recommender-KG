from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uuid

from dl.emotion_inference import infer_emotions  # returns {label: score}
from api.sparql_client import run_select  # existing function in your project

app = FastAPI(title="Neuro-Symbolic Emotion Movie Recommender")

# --- Config ---
DEFAULT_THRESHOLD = 0.5       # industry baseline for GoEmotions multi-label
TOP_K_GENRES = 5              # how many top genres to consider when fetching movies
MOVIES_LIMIT_PER_GENRE = 20   # how many movies to return in total (will be trimmed)

# Map ML emotion label -> ontology genre URIs (must match your ontology prefixes)
# NOTE: keys should match the labels your predictor returns (lowercase). Adjust if necessary.
ONTOLOGY_EMOTION_TO_GENRES = {
    "admiration": ["emo:biography_genre"],
    "amusement": ["emo:comedy_genre"],
    "anger": ["emo:crime_genre", "emo:thriller_genre"],
    "annoyance": ["emo:drama_genre"],
    "approval": ["emo:drama_genre"],
    "caring": ["emo:family_genre"],
    "confusion": ["emo:mystery_genre"],
    "curiosity": ["emo:mystery_genre", "emo:fantasy_genre"],
    "desire": ["emo:romance_genre"],
    "disappointment": ["emo:drama_genre"],
    "disgust": ["emo:horror_genre"],
    "embarrassment": ["emo:drama_genre"],
    "excitement": ["emo:action_genre", "emo:adventure_genre"],
    "fear": ["emo:horror_genre", "emo:thriller_genre"],
    "gratitude": ["emo:uplifting_genre", "emo:family_genre"],
    "grief": ["emo:drama_genre"],
    "joy": ["emo:comedy_genre"],
    "love": ["emo:romance_genre"],
    "nervousness": ["emo:thriller_genre"],
    "optimism": ["emo:family_genre", "emo:uplifting_genre"],
    "pride": ["emo:drama_genre"],
    "realization": ["emo:psychDrama_genre"],
    "relief": ["emo:uplifting_genre"],
    "remorse": ["emo:drama_genre"],
    "sadness": ["emo:drama_genre"],
    "surprise": ["emo:fantasy_genre"],
    "neutral": ["emo:documentary_genre"],
    # add any other labels you use
}

# -----------------------
# Helpers
# -----------------------
def compute_genre_scores(ml_scores: Dict[str, float], threshold: float = DEFAULT_THRESHOLD) -> Dict[str, float]:
    """
    Convert ML emotion probabilities into genre scores.
    - Only emotions with score >= threshold are considered.
    - Scores accumulate additively across emotions that map to the same genre.
    Returns: {genre_uri: score}
    """
    genre_scores: Dict[str, float] = {}
    for emo_label, score in ml_scores.items():
        key = emo_label.lower()
        if score < threshold:
            continue
        genres = ONTOLOGY_EMOTION_TO_GENRES.get(key, [])
        for g in genres:
            genre_scores[g] = genre_scores.get(g, 0.0) + float(score)
    return genre_scores

def top_k_genres_sorted(genre_scores: Dict[str, float], k: int = TOP_K_GENRES) -> List[Dict[str, Any]]:
    """
    Return a sorted list of top-k genres with normalized confidence (0-1).
    """
    if not genre_scores:
        return []
    # normalize by max to produce 0..1 confidences (keeps relative weighting)
    max_score = max(genre_scores.values())
    sorted_items = sorted(genre_scores.items(), key=lambda kv: kv[1], reverse=True)
    top = sorted_items[:k]
    return [{"genre_uri": uri, "raw_score": score, "confidence": round(score / max_score, 3)} for uri, score in top]

def build_movies_query_for_genres(genre_uris: List[str], limit: int = MOVIES_LIMIT_PER_GENRE):
    """
    Build SPARQL SELECT to fetch movies that belong to any of the provided genre URIs.
    genre_uris should be strings like 'emo:comedy_genre'.
    """
    if not genre_uris:
        return None

    genre_list = ", ".join(genre_uris)
    query = f"""
PREFIX emo: <http://www.semanticweb.org/ibrah/ontologies/2025/11/emotion-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?title ?genreLabel WHERE {{
  ?movie a emo:Movie ;
         emo:title ?title ;
         emo:belongsToGenre ?g .
  FILTER (?g IN ({genre_list}))
  OPTIONAL {{ ?g rdfs:label ?genreLabel }}
}}
LIMIT {limit}
"""
    return query

def fetch_movies_for_genres(genre_uris: List[str], limit:int = MOVIES_LIMIT_PER_GENRE) -> List[Dict[str, str]]:
    """
    Query Jena for movies matching the given genre URIs.
    Returns list of {"title":..., "genre":...}
    """
    query = build_movies_query_for_genres(genre_uris, limit)
    if not query:
        return []
    resp = run_select(query)
    bindings = resp.get("results", {}).get("bindings", [])
    movies = []
    for b in bindings:
        title = b.get("title", {}).get("value")
        genreLabel = b.get("genreLabel", {}).get("value") if b.get("genreLabel") else None
        if title:
            movies.append({"title": title, "genre": genreLabel})
    return movies

# -----------------------
# Endpoints
# -----------------------
@app.get("/")
def health():
    return {"status": "ok"}

@app.get("/analyze")
def analyze(text: str, threshold: Optional[float] = DEFAULT_THRESHOLD, top_k: Optional[int] = TOP_K_GENRES):
    """
    Synchronous analyze endpoint (query-parameter style).
    Returns ML scores, computed genre confidences (top_k), and movie list.
    """
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="text must be provided")

    try:
        ml_scores = infer_emotions(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML inference failed: {e}")

    # compute genre weights
    genre_scores = compute_genre_scores(ml_scores, threshold=threshold)
    top_genres = top_k_genres_sorted(genre_scores, k=top_k)

    # fetch movies for top genres (use the URIs)
    genre_uris = [g["genre_uri"] for g in top_genres]
    movies = fetch_movies_for_genres(genre_uris, limit=MOVIES_LIMIT_PER_GENRE)

    return {
        "input": text,
        "ml_scores": ml_scores,
        "genre_scores": top_genres,
        "movies": movies
    }

# Chat-style request/response model
class ChatRequest(BaseModel):
    text: str
    user_id: Optional[str] = None  # optional conversation id (not persisted here)
    threshold: Optional[float] = DEFAULT_THRESHOLD
    top_k: Optional[int] = TOP_K_GENRES

class ChatResponse(BaseModel):
    request_id: str
    reply: str
    ml_scores: Dict[str, float]
    genre_scores: List[Dict[str, Any]]
    movies: List[Dict[str, str]]

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Chat-style endpoint:
    - runs ML -> weighted genres (same logic)
    - returns a short assistant reply string + structured data
    """
    text = req.text
    threshold = req.threshold or DEFAULT_THRESHOLD
    top_k = req.top_k or TOP_K_GENRES

    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="text must be provided")

    # ML
    try:
        ml_scores = infer_emotions(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML inference failed: {e}")

    # compute genre weights and top-k
    genre_scores_dict = compute_genre_scores(ml_scores, threshold=threshold)
    top_genres = top_k_genres_sorted(genre_scores_dict, k=top_k)
    genre_uris = [g["genre_uri"] for g in top_genres]

    # fetch movies
    movies = fetch_movies_for_genres(genre_uris, limit=MOVIES_LIMIT_PER_GENRE)

    # build assistant reply (concise, factual)
    if top_genres:
        top_readable = ", ".join([g["genre_uri"].replace("emo:", "").replace("_genre","").capitalize() for g in top_genres[:3]])
        sample_titles = ", ".join([m["title"] for m in movies[:5]]) if movies else "No titles found"
        reply = f"I detected strongest genre signals for: {top_readable}. Example recommendations: {sample_titles}."
    else:
        reply = "I couldn't confidently detect a dominant emotion-driven genre from that text. Try a different description."

    return ChatResponse(
        request_id=str(uuid.uuid4()),
        reply=reply,
        ml_scores=ml_scores,
        genre_scores=top_genres,
        movies=movies
    )