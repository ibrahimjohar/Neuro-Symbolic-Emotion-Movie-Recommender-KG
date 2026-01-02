from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uuid
import re

from dl.emotion_inference import infer_emotions
from api.sparql_client import run_select
from nlp.emotion_mapper import (
    map_ml_to_ontology_individuals,
    map_ontology_individuals_to_genres
)

app = FastAPI(title="Neuro-Symbolic Emotion Movie Recommender")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MOVIES_LIMIT = 20

EXPLICIT_EMOTION_KEYWORDS = {
    "sad": "sadness",
    "sadness": "sadness",
    "depressed": "sadness",
    "unhappy": "sadness",
    "lonely": "sadness",
    "heartbroken": "sadness",
    "happy": "joy",
    "joyful": "joy",
    "excited": "excitement",
    "angry": "anger",
    "mad": "anger",
    "furious": "anger",
    "scared": "fear",
    "afraid": "fear",
    "anxious": "fear",
}

def detect_explicit_emotion(text: str) -> Optional[str]:
    text_l = text.lower()
    for word, emotion in EXPLICIT_EMOTION_KEYWORDS.items():
        if re.search(rf"\b{word}\b", text_l):
            return emotion
    return None

def build_movies_query(genre_class_uris: List[str], limit: int = MOVIES_LIMIT) -> Optional[str]:
    if not genre_class_uris:
        return None

    values_block = " ".join(genre_class_uris)

    return f"""
    PREFIX emo: <http://www.semanticweb.org/ibrah/ontologies/2025/11/emotion-ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?title ?genreLabel WHERE {{
        VALUES ?genreClass {{ {values_block} }}

        ?movie a emo:Movie ;
               emo:title ?title ;
               emo:belongsToGenre ?genreClass .

        OPTIONAL {{ ?genreClass rdfs:label ?genreLabel }}
    }}
    ORDER BY ?genreLabel ?title
    LIMIT {limit}
    """

def fetch_movies(genre_class_uris: List[str]) -> List[Dict[str, str]]:
    query = build_movies_query(genre_class_uris)
    if not query:
        return []

    try:
        res = run_select(query)
        bindings = res.get("results", {}).get("bindings", [])
        movies = []

        for b in bindings:
            title = b.get("title", {}).get("value")
            genre = b.get("genreLabel", {}).get("value")
            if title:
                movies.append({"title": title, "genre": genre})

        return movies
    except Exception:
        return []
    
def normalize_genre_class(uri: str) -> str:
    if uri.startswith("emo:") and uri.endswith("_genre"):
        base = uri.replace("emo:", "").replace("_genre", "")
        return "emo:" + base.capitalize()
    return uri



class ChatRequest(BaseModel):
    text: str

class ChatResponse(BaseModel):
    request_id: str
    reply: str
    dominant_emotion: str
    genres: List[str]
    movies: List[Dict[str, str]]

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text must be provided")

    explicit_emotion = detect_explicit_emotion(text)

    if explicit_emotion:
        ml_scores = {explicit_emotion: 1.0}
    else:
        ml_scores = infer_emotions(text)

    sorted_scores = sorted(ml_scores.items(), key=lambda x: x[1], reverse=True)
    dominant_emotion = sorted_scores[0][0]

    ontology_inds = map_ml_to_ontology_individuals([dominant_emotion])
    if not ontology_inds:
        return ChatResponse(
            request_id=str(uuid.uuid4()),
            reply="I couldn't map that emotion to any movie genres.",
            dominant_emotion=dominant_emotion,
            genres=[],
            movies=[]
        )

    raw_genres = map_ontology_individuals_to_genres(ontology_inds)
    genre_class_uris = [normalize_genre_class(g) for g in raw_genres]
    
    if not genre_class_uris:
        return ChatResponse(
            request_id=str(uuid.uuid4()),
            reply="I detected the emotion, but couldn't map it to movie genres.",
            dominant_emotion=dominant_emotion,
            genres=[],
            movies=[]
        )

    movies = fetch_movies(genre_class_uris)

    readable_genres = [
        g.replace("emo:", "").replace("_genre", "").capitalize()
        for g in genre_class_uris
    ]

    if movies:
        sample_titles = ", ".join(m["title"] for m in movies[:5])
        reply = (
            f"I detected you're feeling {dominant_emotion}. "
            f"Movies from the {', '.join(readable_genres)} genre might fit your mood. "
            f"Here are some examples: {sample_titles}."
        )
    else:
        reply = (
            f"I detected you're feeling {dominant_emotion}. "
            f"I identified the {', '.join(readable_genres)} genre, "
            f"but couldn't find matching movies in the database."
        )

    return ChatResponse(
        request_id=str(uuid.uuid4()),
        reply=reply,
        dominant_emotion=dominant_emotion,
        genres=readable_genres,
        movies=movies
    )
