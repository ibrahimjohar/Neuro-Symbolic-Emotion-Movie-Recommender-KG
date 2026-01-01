from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uuid

from dl.emotion_inference import infer_emotions  # returns {label: score}
from api.sparql_client import run_select  # existing function in your project
from nlp.emotion_dominance import select_dominant_emotions
from nlp.emotion_mapper import (
    map_ml_to_ontology_individuals,
    map_ontology_individuals_to_genres
)

app = FastAPI(title="Neuro-Symbolic Emotion Movie Recommender")

# --- Config ---
DEFAULT_THRESHOLD = 0.5       # industry baseline for GoEmotions multi-label
TOP_K_GENRES = 5              # how many top genres to consider when fetching movies
MOVIES_LIMIT_PER_GENRE = 20   # how many movies to return in total (will be trimmed)

# Map ML emotion label -> ontology genre URIs (must match your ontology prefixes)
# NOTE: keys should match the labels your predictor returns (lowercase). Adjust if necessary.
# IMPORTANT: Genre classes in KG are capitalized (emo:Comedy, emo:Drama) NOT lowercase with _genre suffix
ONTOLOGY_EMOTION_TO_GENRES = {
    "admiration": ["emo:Drama"],  # Biography not in movies, use Drama
    "amusement": ["emo:Comedy"],
    "anger": ["emo:Crime", "emo:Thriller"],
    "annoyance": ["emo:Drama"],
    "approval": ["emo:Drama"],
    "caring": ["emo:Family"],
    "confusion": ["emo:Drama"],  # Mystery not in movies, use Drama
    "curiosity": ["emo:Drama", "emo:Fantasy"],  # Mystery not in movies, use Drama
    "desire": ["emo:Romance"],
    "disappointment": ["emo:Drama"],
    "disgust": ["emo:Horror"],
    "embarrassment": ["emo:Drama"],
    "excitement": ["emo:Action", "emo:Adventure"],
    "fear": ["emo:Horror", "emo:Thriller"],
    "gratitude": ["emo:Family", "emo:Drama"],  # Uplifting not in movies, use Drama
    "grief": ["emo:Drama"],
    "joy": ["emo:Comedy"],
    "love": ["emo:Romance"],
    "nervousness": ["emo:Thriller"],
    "optimism": ["emo:Family", "emo:Drama"],  # Uplifting not in movies, use Drama
    "pride": ["emo:Drama"],
    "realization": ["emo:Drama"],  # PsychologicalDrama not in movies, use Drama
    "relief": ["emo:Drama"],  # Uplifting not in movies, use Drama
    "remorse": ["emo:Drama"],
    "sadness": ["emo:Drama"],
    "surprise": ["emo:Fantasy"],
    "neutral": ["emo:Drama"],  # Documentary not in movies, use Drama
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
    genre_uris should be strings like 'emo:Comedy', 'emo:Drama' (capitalized, no _genre suffix).
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
    print(f"DEBUG build_movies_query: genre_uris={genre_uris}, query={query}")
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

    # Initialize variables
    movies = []
    top_genres = []
    
    # ML
    try:
        ml_scores = infer_emotions(text)   # returns {label:score}
        print("DEBUG ML scores:", ml_scores)

        dominant_emotions = select_dominant_emotions(
            ml_scores,
            top_k=2,
            min_prob=0.15
        )
        print("DEBUG dominant_emotions:", dominant_emotions)

        ontology_inds = map_ml_to_ontology_individuals(dominant_emotions)
        print("DEBUG ontology_inds:", ontology_inds)

        # Try SPARQL query if we have ontology individuals, otherwise use fallback
        if ontology_inds:
            # Build the VALUES block for SPARQL: e.g. VALUES ?emotionInd { emo:joy_1 emo:fear_1 }
            # Format ontology individuals with proper prefix
            values_block = " ".join([f"emo:{ind}" for ind in ontology_inds])
            
            # Use user_id from request if provided, otherwise default to text_test
            text_individual = f"emo:{req.user_id}" if req.user_id else "emo:text_test"

            query = f"""
            PREFIX emo: <http://www.semanticweb.org/ibrah/ontologies/2025/11/emotion-ontology#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT DISTINCT ?title ?genreLabel
            WHERE {{
            VALUES ?emotionInd {{ {values_block} }}

            # two ways to find genre classes:
            {{
                # if text individual has expressesEmotion ?emotionInd AND also suggestsGenre assertions created already
                {text_individual} emo:expressesEmotion ?emotionInd .
                {text_individual} emo:suggestsGenre ?genreInd .
            }} UNION {{
                # or if the emotion individual itself has direct suggestsGenre -> genreInd
                ?emotionInd emo:suggestsGenre ?genreInd .
            }}

            ?genreInd rdf:type ?genreClass .
            ?genreClass rdfs:label ?genreLabel .

            ?movie a emo:Movie ;
                    emo:title ?title ;
                    emo:belongsToGenre ?genreClass .
            }}
            ORDER BY ?genreLabel ?title
            LIMIT 50
            """
            print("DEBUG SPARQL query:", query)
            
            # Actually execute the SPARQL query
            try:
                sparql_response = run_select(query)
                print("DEBUG SPARQL response:", sparql_response)
                
                # Parse SPARQL results
                bindings = sparql_response.get("results", {}).get("bindings", [])
                sparql_movies = []
                
                for b in bindings:
                    title = b.get("title", {}).get("value")
                    genreLabel = b.get("genreLabel", {}).get("value") if b.get("genreLabel") else None
                    if title:
                        sparql_movies.append({"title": title, "genre": genreLabel})
                
                # If we got results from SPARQL, use them
                if sparql_movies:
                    movies = sparql_movies
                    print(f"DEBUG: Found {len(movies)} movies from SPARQL query")
                else:
                    print("DEBUG: SPARQL query returned no movies, will use genre-based fallback")
                    
            except Exception as sparql_error:
                # If SPARQL query fails, will use fallback below
                print(f"DEBUG: SPARQL query failed: {sparql_error}, will use genre-based fallback")
        else:
            print("DEBUG: No ontology individuals found, using genre-based approach")
        
        # Always compute genre scores (needed for response)
        # Use a lower threshold if the default one filters everything out
        genre_scores_dict = compute_genre_scores(ml_scores, threshold=threshold)
        
        # If threshold is too high and filters everything, use a lower threshold
        if not genre_scores_dict and threshold >= 0.3:
            print(f"DEBUG: Threshold {threshold} filtered all emotions, trying lower threshold 0.2")
            genre_scores_dict = compute_genre_scores(ml_scores, threshold=0.2)
        
        # If still empty, use top emotions by score (no threshold)
        if not genre_scores_dict:
            print("DEBUG: Still no genre scores, using top emotions without threshold")
            # Get top emotions by raw score
            sorted_emotions = sorted(ml_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
            # Manually build genre scores from top emotions
            for emo_label, score in sorted_emotions:
                key = emo_label.lower()
                genres = ONTOLOGY_EMOTION_TO_GENRES.get(key, [])
                for g in genres:
                    genre_scores_dict[g] = genre_scores_dict.get(g, 0.0) + float(score)
        
        top_genres = top_k_genres_sorted(genre_scores_dict, k=top_k)
        print(f"DEBUG: top_genres count: {len(top_genres)}")
        
        # If we don't have movies from SPARQL, use the working genre-based approach
        if not movies:
            if top_genres:
                genre_uris = [g["genre_uri"] for g in top_genres]
                print(f"DEBUG: Fetching movies for genres: {genre_uris}")
                movies = fetch_movies_for_genres(genre_uris, limit=MOVIES_LIMIT_PER_GENRE)
                print(f"DEBUG: Fetched {len(movies)} movies")
            else:
                print("DEBUG: No top_genres available, cannot fetch movies")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML inference failed: {e}")

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