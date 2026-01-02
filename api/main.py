from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uuid
import re

from dl.emotion_inference import infer_emotions
from api.sparql_client import run_select
from session_state import update_session, dominant_emotions

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

def rank_movies(movies, top_emotions):
    #if no top_emotions, return movies unchanged
    if not top_emotions:
        return movies

    #simple stable ranking placeholder that does not mutate movie dicts.
    #(keep ontology as ground truth, python only reorders.)
    #for now sort by title so output is deterministic.
    return sorted(movies, key=lambda m: (m.get("title") or "").lower())

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
    
    session_id = req.request_id if hasattr(req, "request_id") else "default"

    ml_scores = infer_emotions(text)
    if explicit_emotion:
        ml_scores[explicit_emotion] = max(ml_scores.get(explicit_emotion, 0.0), 0.75)

    session_scores = update_session(session_id, ml_scores)
    top_emotions = dominant_emotions(session_scores)
    dominant_emotion = top_emotions[0][0]


    query = f"""
            PREFIX emo: <http://www.semanticweb.org/ibrah/ontologies/2025/11/emotion-ontology#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT DISTINCT ?title ?genreLabel WHERE {{
                emo:text_test emo:suggestsGenre ?genreInd .

                ?genreInd rdf:type ?genreClass .
                OPTIONAL {{ ?genreClass rdfs:label ?genreLabel }}

                ?movie a emo:Movie ;
                    emo:title ?title ;
                    emo:belongsToGenre ?genreClass .
            }}
            LIMIT {MOVIES_LIMIT}
            """
    
    res = run_select(query)
    bindings = res.get("results", {}).get("bindings", [])

    movies = []
    genres = set()

    for b in bindings:
        title = b.get("title", {}).get("value")
        genre = b.get("genreLabel", {}).get("value")
        if title:
            movies.append({"title": title, "genre": genre})
        if genre:
            genres.add(genre)

    genres = list(genres)
    
    movies = rank_movies(movies, top_emotions)
    
    if movies:
        sample_titles = ", ".join(m["title"] for m in movies[:5])
        reply = (
            f"I detected you're feeling {dominant_emotion}. "
            f"Based on inferred genres {', '.join(genres)}, "
            f"here are some matching movies: {sample_titles}."
        )
    else:
        reply = (
            f"Based on your recent emotions ({', '.join(e for e, _ in top_emotions)}), "
            f"and genres inferred by the ontology, here are some recommendations."
        )

        
    return ChatResponse(
        request_id=str(uuid.uuid4()),
        reply=reply,
        dominant_emotion=dominant_emotion,
        genres=genres,
        movies=movies
    )


