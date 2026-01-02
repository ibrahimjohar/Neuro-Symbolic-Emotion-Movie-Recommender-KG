from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from collections import Counter
import uuid
import re

from dl.emotion_inference import infer_emotions
from api.sparql_client import run_select
from session_state import update_emotions, aggregated_emotions, is_confident_enough
from nlp.emotion_genre_map import EMOTION_TO_GENRES
from nlp.emotion_mapper import EMOTION_TO_ONTOLOGY

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
    
    #session_id = req.request_id if hasattr(req, "request_id") else "default"
    session_id = "default"

    ml_scores = infer_emotions(text)
    if explicit_emotion:
        ml_scores[explicit_emotion] = max(ml_scores.get(explicit_emotion, 0.0), 0.75)

    #update session with current emotion inference
    update_emotions(session_id, ml_scores)

    #aggregate over turns
    agg_emotions = aggregated_emotions(session_id)

    #sort by strength
    top_emotions = sorted(
        agg_emotions.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    top_emotions = [(e, w) for e, w in top_emotions if e != "neutral"]
    
    dominant_emotion = top_emotions[0][0] if top_emotions else "neutral"
    
    print("TOP_EMOTIONS:", top_emotions)
    for emo_label, w in top_emotions:
        emo_ind = EMOTION_TO_ONTOLOGY.get(emo_label)
        emo_key = f"emo:{emo_ind}" if emo_ind else None
        print("MAP:", emo_label, "->", emo_key, "IN_GENRE_MAP:", emo_key in EMOTION_TO_GENRES)

    print("GENRE_MAP_KEYS_SAMPLE:", list(EMOTION_TO_GENRES.keys())[:8])
    
    genre_counter = Counter()

    for emo_label, weight in top_emotions:
        emo_local = EMOTION_TO_ONTOLOGY.get(emo_label)

        if not emo_local:
            continue

        emo_key = emo_local if emo_local.startswith("emo:") else f"emo:{emo_local}"

        print(
            "RANKING MAP:",
            emo_label,
            "->",
            emo_key,
            "IN_GENRE_MAP:",
            emo_key in EMOTION_TO_GENRES
        )

        for genre in EMOTION_TO_GENRES.get(emo_key, []):
            genre_counter[genre] += weight

    
    ranked_genres = [g for g, _ in genre_counter.most_common(3)]
    
    if not ranked_genres:
        return ChatResponse(
            request_id=str(uuid.uuid4()),
            reply="I detected emotions, but the ontology did not prioritize any genres yet.",
            dominant_emotion=dominant_emotion,
            genres=[],
            movies=[]
        )
        
    if not is_confident_enough(session_id):
        return ChatResponse(
            request_id=str(uuid.uuid4()),
            reply=(
                "I’m still getting a better sense of how you’re feeling. "
                "Can I ask you another quick question?"
            ),
            dominant_emotion=top_emotions[0][0] if top_emotions else "neutral",
            genres=[],
            movies=[]
        )


    values_block = " ".join(ranked_genres)

    query = f"""
        PREFIX emo: <http://www.semanticweb.org/ibrah/ontologies/2025/11/emotion-ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT DISTINCT ?title ?genreLabel WHERE {{
        VALUES ?genreClass {{ {values_block} }}

        ?movie a emo:Movie ;
                emo:title ?title ;
                emo:belongsToGenre ?genreClass .

        OPTIONAL {{ ?genreClass rdfs:label ?genreLabel }}
        }}
        LIMIT {MOVIES_LIMIT}
        """

    res = run_select(query)
    bindings = res.get("results", {}).get("bindings", [])

    movies = []
    genres = set()
    for b in bindings:
        title = b.get("title", {}).get("value")
        genre = b.get("genreLabel", {}).get("value", "")
        if title:
            movies.append({"title": title, "genre": genre})
        if genre:
            genres.add(genre)

    genres = [g.replace("emo:", "") for g in ranked_genres]
    
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
            f"Based on your recent emotions "
            f"({', '.join(e for e, _ in top_emotions)}), "
            f"I prioritized genres inferred by the ontology."
        )

        
    return ChatResponse(
        request_id=str(uuid.uuid4()),
        reply=reply,
        dominant_emotion=dominant_emotion,
        genres=genres,
        movies=movies
    )


