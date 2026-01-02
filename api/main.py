from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic import ConfigDict
from typing import List, Dict, Optional
import uuid
import re
import logging
import random
import os
import requests

from dl.emotion_inference import infer_emotions
from nlp.emotion_mapper import map_ml_to_ontology_individuals, EMOTION_TO_ONTOLOGY
from nlp.emotion_genre_map import EMOTION_TO_GENRES
from nlp.followup_questions import FOLLOWUP_QUESTIONS
from api.sparql_client import run_select
from session_state import update_emotions, aggregated_emotions, is_confident_enough, get_pending_question, set_pending_question, clear_pending_question, get_slots, set_slot_value, filled_slot_count, get_seen_titles, add_seen_titles
import json

app = FastAPI()

# Basic logger
logger = logging.getLogger("api")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"]
    ,
    allow_headers=["*"]
)

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    text: str
    threshold: Optional[float] = None
    top_k: Optional[int] = None
    model_config = ConfigDict(extra='ignore')

class ChatResponse(BaseModel):
    request_id: str
    reply: str
    dominant_emotion: str
    genres: List[str]
    movies: List[Dict[str, str]]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(req: ChatRequest) -> ChatResponse:
    try:
        if not req.text or not req.text.strip():
            raise HTTPException(status_code=400, detail="Text must be provided")

        session_id = req.session_id or req.user_id or "default"
        text = req.text.strip()

        # quick genre hint extraction from free text
        def extract_genre_hint(t: str) -> Optional[str]:
            _load_genre_labels()
            _load_genre_synonyms()
            s_norm = _normalize_simple(t)
            # 1) direct match against ontology labels/forms
            for form, curie in GENRE_FORMS_CACHE.items():
                if form and form in s_norm:
                    return curie
            # 2) synonym match loaded from ontology-aligned data
            for syn, curie in GENRE_SYNONYMS_CACHE.items():
                if syn and syn in s_norm:
                    return curie
            return None

        genre_hint = extract_genre_hint(text)

        # 1) Model inference (resilient)
        try:
            ml_scores = infer_emotions(text)
        except Exception as e:
            logger.error(f"Emotion inference failed: {e}")
            ml_scores = {}

        # 2) Update session state and aggregate
        update_emotions(session_id, ml_scores)
        agg_emotions = aggregated_emotions(session_id)

        # 3) Pick dominant emotion (simple heuristic)
        top_emotions = sorted(agg_emotions.items(), key=lambda x: x[1], reverse=True)
        top_emotions = [e for e, _ in top_emotions][:3]
        dominant_emotion = top_emotions[0] if top_emotions else "neutral"

        # 4) Handle pending follow-up: interpret answer and proceed
        pending = get_pending_question(session_id)
        selected_individual = None
        if pending:
            selected_value = interpret_followup_answer(pending, text, ml_scores)
            if selected_value:
                # store the slot value and use it if it's an ontology individual
                set_slot_value(session_id, pending, selected_value)
                if isinstance(selected_value, str) and selected_value.startswith("emo:"):
                    selected_individual = selected_value
            clear_pending_question(session_id)
            # If user answered a different slot implicitly, capture it too
            if not selected_value:
                det = detect_any_slot_value(text, ml_scores)
                if det:
                    sid, val = det
                    set_slot_value(session_id, sid, val)

        # decide next slot if needed
        slots = get_slots(session_id)
        def _next_slot():
            # adaptive flow based on emotion_direction
            direction = slots.get("emotion_direction")
            base_flow = ["emotion_direction", "desired_outcome", "pace_preference", "violence_tolerance", "era_preference", "content_sensitivity"]
            intense_flow = ["emotion_direction", "intensity_style", "desired_outcome", "pace_preference", "violence_tolerance", "era_preference", "content_sensitivity"]
            comfort_flow = ["emotion_direction", "comfort_style", "desired_outcome", "pace_preference", "violence_tolerance", "era_preference", "content_sensitivity"]
            flow = intense_flow if direction == "intense" else comfort_flow if direction == "comforting" else base_flow
            for s in flow:
                if s not in slots:
                    return s
            return None

        progress_confident = is_confident_enough(session_id) or filled_slot_count(session_id) >= 2

        # 5) If we are not confident and no interpreted answer, ask next follow-up slot
        if not selected_individual and not progress_confident:
            pending = get_pending_question(session_id)
            if not pending:
                pending = _next_slot() or "emotion_direction"
                set_pending_question(session_id, pending)
            fq = FOLLOWUP_QUESTIONS.get(pending, {})
            variants = fq.get("variants")
            question = random.choice(variants) if isinstance(variants, list) and variants else fq.get("question", "Could you tell me more about your mood?")
            return ChatResponse(
                request_id=str(uuid.uuid4()),
                reply=question,
                dominant_emotion=dominant_emotion,
                genres=[],
                movies=[],
            )

        # 6) Map emotion to ontology individuals / genres (use slots first)
        if not selected_individual:
            # pick any previously filled slot that maps to an ontology individual
            for s in ["desired_outcome", "emotion_direction", "cognitive_load"]:
                v = slots.get(s)
                if isinstance(v, str) and v.startswith("emo:"):
                    selected_individual = v
                    break
        if not selected_individual:
            if dominant_emotion in EMOTION_TO_ONTOLOGY:
                selected_individual = EMOTION_TO_ONTOLOGY[dominant_emotion]
        individuals = map_ml_to_ontology_individuals(top_emotions) or ([])
        if not selected_individual and individuals:
            selected_individual = individuals[0]

        ranked_genres = EMOTION_TO_GENRES.get(selected_individual or "", [])

        # if user gave a genre hint, prioritize it
        if genre_hint and genre_hint not in ranked_genres:
            ranked_genres = [genre_hint] + ranked_genres

        # apply content sensitivity filtering
        sensitivity = slots.get("content_sensitivity")
        if sensitivity == "avoid_horror":
            ranked_genres = [g for g in ranked_genres if "Horror" not in g]
        elif sensitivity == "avoid_drama":
            ranked_genres = [g for g in ranked_genres if "Drama" not in g]
        elif sensitivity == "avoid_violence":
            ranked_genres = [g for g in ranked_genres if ("Action" not in g and "Crime" not in g and "War" not in g)]

        # 7) Query movies from KG via SPARQL (aligned predicates)
        # filter to concrete genre classes that exist in the KG
        _load_genre_labels()
        allowed_genres = set(GENRE_LABELS_CACHE.keys())
        # compute genre weights from slots to build ranked list
        base_genres = list(allowed_genres)
        weights = {g: 1.0 for g in base_genres}
        # desired outcome
        if slots.get("desired_outcome") == "get_excited":
            for g in ["emo:Action","emo:Thriller","emo:SciFi"]: weights[g] += 0.8
        elif slots.get("desired_outcome") == "feel_better":
            for g in ["emo:Comedy","emo:Family","emo:Romance"]: weights[g] += 0.8
        elif slots.get("desired_outcome") == "process_feelings":
            for g in ["emo:Drama","emo:Documentary"]: weights[g] += 0.8
        # intensity/comfort style
        if slots.get("intensity_style") == "adrenaline":
            for g in ["emo:Action","emo:Thriller","emo:Adventure"]: weights[g] += 0.7
        elif slots.get("intensity_style") == "suspense":
            for g in ["emo:Thriller","emo:Mystery","emo:Crime"]: weights[g] += 0.7
        elif slots.get("intensity_style") == "dark":
            for g in ["emo:Horror","emo:Crime","emo:FilmNoir"]: weights[g] += 0.7
        if slots.get("comfort_style") == "uplifting":
            for g in ["emo:Comedy","emo:Family","emo:Romance"]: weights[g] += 0.7
        elif slots.get("comfort_style") == "heartwarming":
            for g in ["emo:Family","emo:Romance","emo:Drama"]: weights[g] += 0.6
        elif slots.get("comfort_style") == "calm":
            for g in ["emo:Drama","emo:Documentary","emo:Fantasy"]: weights[g] += 0.5
        # cognitive load
        if slots.get("cognitive_load") == "escapist":
            for g in ["emo:Fantasy","emo:Comedy","emo:Adventure"]: weights[g] += 0.6
        elif slots.get("cognitive_load") == "thoughtful":
            for g in ["emo:Drama","emo:Mystery","emo:Documentary"]: weights[g] += 0.6
        # pace
        if slots.get("pace_preference") == "fast":
            for g in ["emo:Action","emo:Thriller","emo:Adventure"]: weights[g] += 0.6
        elif slots.get("pace_preference") == "slow":
            for g in ["emo:Drama","emo:Mystery","emo:Western"]: weights[g] += 0.6
        # violence tolerance
        vt = slots.get("violence_tolerance")
        if vt == "none":
            for g in ["emo:Action","emo:Crime","emo:War","emo:Horror"]: weights[g] -= 0.7
        elif vt == "mild":
            for g in ["emo:Action","emo:Crime","emo:War","emo:Horror"]: weights[g] -= 0.3
        # content sensitivity filter
        sensitivity = slots.get("content_sensitivity")
        if sensitivity == "avoid_horror":
            for g in ["emo:Horror"]: weights[g] -= 1.0
        elif sensitivity == "avoid_drama":
            for g in ["emo:Drama"]: weights[g] -= 0.8
        elif sensitivity == "avoid_violence":
            for g in ["emo:Action","emo:Crime","emo:War"]: weights[g] -= 0.9

        # helper: diversify candidates by era, avoid repeats, and apply comfort blocking
        def _diversify_candidates(candidates_list):
            seen = set(get_seen_titles(session_id))
            k = req.top_k or 5
            era_pref = slots.get("era_preference")

            # block harsher genres for comfort-first scenarios
            direction = slots.get("emotion_direction")
            outcome = slots.get("desired_outcome")
            cstyle = slots.get("comfort_style")
            blocked = set()
            if direction == "comforting" or outcome == "feel_better" or cstyle in {"calm", "heartwarming"}:
                blocked = {"Horror", "War", "Crime"}

            def _is_blocked(c):
                if not blocked:
                    return False
                full = c.get("genres_full")
                if isinstance(full, list):
                    lf = {g.lower() for g in full}
                    return any(b.lower() in lf for b in blocked)
                g = c.get("genre", "")
                return g in blocked

            # filter blocked upfront
            filtered = [c for c in candidates_list if not _is_blocked(c)]

            # prefer unseen titles; backfill with seen if needed
            unseen = [c for c in filtered if c.get("title") not in seen]
            seen_list = [c for c in filtered if c.get("title") in seen]

            def _to_int_year(y):
                try:
                    return int(str(y))
                except Exception:
                    return 0

            def _mix_by_era(pool):
                modern = [c for c in pool if _to_int_year(c.get("year")) >= 1990]
                classic = [c for c in pool if _to_int_year(c.get("year")) < 1990]
                modern.sort(key=lambda x: x.get("score", 0.0), reverse=True)
                classic.sort(key=lambda x: x.get("score", 0.0), reverse=True)
                if era_pref == "classic":
                    primary, secondary = classic, modern
                elif era_pref == "modern":
                    primary, secondary = modern, classic
                else:
                    primary, secondary = modern, classic
                take_primary = k // 2 if secondary else k
                take_secondary = k - take_primary
                sel = []
                sel.extend(primary[:take_primary])
                sel.extend(secondary[:take_secondary])
                if len(sel) < k:
                    remaining = [c for c in pool if c not in sel]
                    remaining.sort(key=lambda x: x.get("score", 0.0), reverse=True)
                    sel.extend(remaining[:k - len(sel)])
                return sel[:k]

            selected = _mix_by_era(unseen)
            if len(selected) < k:
                selected.extend([c for c in _mix_by_era(seen_list) if c not in selected][:k - len(selected)])

            random.shuffle(selected)
            return [{"title": s.get("title", ""), "genre": s.get("genre", ""), "year": s.get("year", "")} for s in selected[:k]]

        # seed with emotion-derived genres if available
        seed = EMOTION_TO_GENRES.get(selected_individual or "", [])
        for g in seed:
            if g in weights:
                weights[g] += 0.5

        # finalize ranked list
        ranked_genres = [g for g, w in sorted(weights.items(), key=lambda x: x[1], reverse=True) if w > 0]

        values_block = " ".join(f"({g})" for g in ranked_genres)

        era = slots.get("era_preference")
        year_filter = ""
        if era == "classic":
            year_filter = "FILTER(xsd:integer(?year) < 1990)"
        elif era == "modern":
            year_filter = "FILTER(xsd:integer(?year) >= 1990)"

        query = f"""
        PREFIX emo: <http://www.semanticweb.org/ibrah/ontologies/2025/11/emotion-ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT ?title ?year ?genre ?genreLabel WHERE {{
          {f"VALUES (?genre) {{ {values_block} }}" if values_block else ""}
          ?m a emo:Movie ; emo:hasTitle ?title ; emo:hasYear ?year {"; emo:belongsToGenre ?genre ." if values_block else "."}
          OPTIONAL {{ ?genre rdfs:label ?genreLabel }}
          {year_filter}
        }} LIMIT {req.top_k or 5}
        """

        movies = []
        try:
            sparql_res = run_select(query, timeout=15)
            candidates_map = {}
            for b in sparql_res.get("results", {}).get("bindings", []):
                title = b.get("title", {}).get("value", "")
                year = b.get("year", {}).get("value", "")
                genre_uri = b.get("genre", {}).get("value", "")
                genre_label = b.get("genreLabel", {}).get("value", "")
                curie = None
                if genre_uri and genre_uri.startswith(ONTO_BASE):
                    local = genre_uri[len(ONTO_BASE):]
                    curie = f"emo:{local}"
                if curie is None:
                    continue
                w = weights.get(curie, 0.0)
                entry = candidates_map.setdefault(title, {"title": title, "year": year, "genre": genre_label, "score": 0.0, "best_w": -1.0, "genres_full": set()})
                entry["score"] += w
                entry["genres_full"].add(genre_label)
                if w > entry["best_w"]:
                    entry["best_w"] = w
                    entry["genre"] = genre_label
            candidates = []
            for v in candidates_map.values():
                if isinstance(v.get("genres_full"), set):
                    v["genres_full"] = list(v["genres_full"])
                candidates.append(v)
            movies = _diversify_candidates(candidates)
        except Exception as e:
            logger.error(f"SPARQL query failed: {e}")

        if not movies:
            query_relaxed = f"""
            PREFIX emo: <http://www.semanticweb.org/ibrah/ontologies/2025/11/emotion-ontology#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            SELECT ?title ?year WHERE {{
              ?m a emo:Movie ; emo:hasTitle ?title ; emo:hasYear ?year .
              {year_filter}
            }} LIMIT {req.top_k or 5}
            """
            try:
                sparql_res = run_select(query_relaxed, timeout=15)
                candidates = []
                for b in sparql_res.get("results", {}).get("bindings", []):
                    title = b.get("title", {}).get("value", "")
                    year = b.get("year", {}).get("value", "")
                    candidates.append({"title": title, "genre": "", "year": year, "score": 0.5})
                movies = _diversify_candidates(candidates)
            except Exception as e:
                logger.error(f"Era-only SPARQL failed: {e}")

        if not movies:
            broad_query = f"""
            PREFIX emo: <http://www.semanticweb.org/ibrah/ontologies/2025/11/emotion-ontology#>
            SELECT ?title ?year WHERE {{
              ?m a emo:Movie ; emo:hasTitle ?title ; emo:hasYear ?year .
            }} LIMIT {req.top_k or 5}
            """
            try:
                sparql_res = run_select(broad_query, timeout=15)
                candidates = []
                for b in sparql_res.get("results", {}).get("bindings", []):
                    title = b.get("title", {}).get("value", "")
                    year = b.get("year", {}).get("value", "")
                    candidates.append({"title": title, "genre": "", "year": year, "score": 0.3})
                movies = _diversify_candidates(candidates)
            except Exception as e:
                logger.error(f"Broad SPARQL query failed: {e}")

        if not movies:
            try:
                with open("data/movie_kb_final.csv", "r", encoding="utf-8") as f:
                    import csv
                    rdr = csv.DictReader(f, fieldnames=["id","title","year","genres"])
                    next(rdr, None)
                    candidates = []
                    for row in rdr:
                        try:
                            title = row.get("title", "")
                            year = row.get("year", "")
                            genres_norm = row.get("genres", "")
                            if not title:
                                continue
                            genre_list = [g.strip() for g in genres_norm.split("|") if g.strip()]
                            score = 0.0
                            best_label = ""
                            best_w = -1.0
                            for gname in genre_list:
                                _load_genre_labels()
                                curie = None
                                gl = gname.lower()
                                for k, v in GENRE_LABELS_CACHE.items():
                                    if v.lower() == gl:
                                        curie = k
                                        break
                                if curie is None:
                                    curie = f"emo:{re.sub('[^A-Za-z0-9]', '', gname)}"
                                w = weights.get(curie, 0.0)
                                score += w
                                if w > best_w:
                                    best_w = w
                                    best_label = gname
                            candidates.append({"title": title, "genre": best_label or (genre_list[0] if genre_list else ""), "year": year, "score": score, "genres_full": genre_list})
                        except Exception:
                            continue
                    movies = _diversify_candidates(candidates)
            except Exception as e:
                logger.error(f"CSV fallback failed: {e}")

        clear_pending_question(session_id)
        try:
            add_seen_titles(session_id, [m.get("title", "") for m in movies])
        except Exception:
            pass
        return ChatResponse(
            request_id=str(uuid.uuid4()),
            reply="Here are some movies you may like:",
            dominant_emotion=dominant_emotion,
            genres=ranked_genres,
            movies=movies,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unhandled error in /chat: {e}")
        return ChatResponse(
            request_id=str(uuid.uuid4()),
            reply=(
                "Sorry, I hit an unexpected issue. Tell me a genre (e.g., 'Comedy') "
                "or how you're feeling, and I'll suggest films."
            ),
            dominant_emotion="neutral",
            genres=[],
            movies=[],
        )

def _normalize_text(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\s+", " ", s)
    return s

SLOT_ORDER = [
    "emotion_direction",
    "desired_outcome",
    "pace_preference",
    "violence_tolerance",
    "era_preference",
    "content_sensitivity",
]

def interpret_followup_answer(pending_id: str, user_text: str, ml_scores: Dict[str, float]) -> Optional[str]:
    t = _normalize_text(user_text)
    synonyms = {
        "emotion_direction": {
            "comforting": [
                "comfort", "comforting", "light", "happy", "calm", "gentle",
                "soothing", "feel better", "uplifting", "positive", "warm",
                "heartwarming", "wholesome"
            ],
            "intense": [
                "intense", "dark", "thrill", "thrilling", "scary", "horror",
                "action", "sad", "dramatic", "serious", "heavy"
            ],
        },
        "desired_outcome": {
            "feel_better": ["feel better", "lift mood", "uplift", "cheer up"],
            "process_feelings": ["process feelings", "reflect", "think", "ponder"],
            "get_excited": ["get excited", "pump", "adrenaline", "thrill"],
        },
        "era_preference": {
            "classic": ["classic", "older", "vintage", "retro"],
            "modern": ["modern", "newer", "recent", "contemporary"],
        },
        "content_sensitivity": {
            "avoid_horror": ["avoid horror", "no horror", "not horror"],
            "avoid_drama": ["avoid drama", "no drama", "not drama", "heavy"],
            "avoid_violence": ["avoid violence", "no violence", "not violent", "no action"],
        },
        "intensity_style": {
            "adrenaline": ["adrenaline", "adrenaline pumping", "pump", "exciting", "high octane"],
            "suspense": ["suspense", "tense", "edge of seat", "thriller"],
            "dark": ["dark", "edgy", "grisly", "grim", "horror"],
        },
        "comfort_style": {
            "uplifting": ["uplifting", "feel good", "cheer up", "positive"],
            "heartwarming": ["heartwarming", "warm", "wholesome"],
            "calm": ["calm", "soothing", "relaxing", "low stakes", "calming", "gentle"],
        },
        "pace_preference": {
            "fast": ["fast", "fast paced", "quick", "rapid"],
            "slow": ["slow", "slow burn", "steady"],
        },
        "violence_tolerance": {
            "none": ["no violence", "avoid violence"],
            "mild": ["mild", "some", "a little"],
            "strong": ["strong", "high", "ok with violence"],
        }
    }
    for slot_id, opts in synonyms.items():
        for value, words in opts.items():
            if any(w in t for w in words):
                return f"emo:{value}" if slot_id in {"desired_outcome","emotion_direction","cognitive_load"} else value
    joy_dom = (ml_scores.get("joy", 0) + ml_scores.get("admiration", 0))
    fear_dom = (ml_scores.get("fear", 0) + ml_scores.get("anger", 0))
    if joy_dom or fear_dom:
        val = "comforting" if joy_dom >= fear_dom else "intense"
        return f"emo:{val}"
    return None

from typing import Tuple

def detect_any_slot_value(user_text: str, ml_scores: Dict[str, float]) -> Optional[Tuple[str, str]]:
    t = _normalize_text(user_text)
    synonyms = {
        "emotion_direction": {
            "comforting": [
                "comfort", "comforting", "light", "happy", "calm", "gentle",
                "soothing", "feel better", "uplifting", "positive", "warm",
                "heartwarming", "wholesome"
            ],
            "intense": [
                "intense", "dark", "thrill", "thrilling", "scary", "horror",
                "action", "sad", "dramatic", "serious", "heavy"
            ],
        },
        "desired_outcome": {
            "feel_better": ["feel better", "lift mood", "uplift", "cheer up"],
            "process_feelings": ["process feelings", "reflect", "think", "ponder"],
            "get_excited": ["get excited", "pump", "adrenaline", "thrill"],
        },
        "era_preference": {
            "classic": ["classic", "older", "vintage", "retro"],
            "modern": ["modern", "newer", "recent", "contemporary"],
        },
        "content_sensitivity": {
            "avoid_horror": ["avoid horror", "no horror", "not horror"],
            "avoid_drama": ["avoid drama", "no drama", "not drama", "heavy"],
            "avoid_violence": ["avoid violence", "no violence", "not violent", "no action"],
        },
        "intensity_style": {
            "adrenaline": ["adrenaline", "adrenaline pumping", "pump", "exciting", "high octane"],
            "suspense": ["suspense", "tense", "edge of seat", "thriller"],
            "dark": ["dark", "edgy", "grisly", "grim", "horror"],
        },
        "comfort_style": {
            "uplifting": ["uplifting", "feel good", "cheer up", "positive"],
            "heartwarming": ["heartwarming", "warm", "wholesome"],
            "calm": ["calm", "soothing", "relaxing", "low stakes", "calming", "gentle"],
        },
        "pace_preference": {
            "fast": ["fast", "fast paced", "quick", "rapid"],
            "slow": ["slow", "slow burn", "steady"],
        },
        "violence_tolerance": {
            "none": ["no violence", "avoid violence"],
            "mild": ["mild", "some", "a little"],
            "strong": ["strong", "high", "ok with violence"],
        }
    }
    for slot_id, opts in synonyms.items():
        for value, words in opts.items():
            if any(w in t for w in words):
                return (slot_id, value)
    joy_dom = (ml_scores.get("joy", 0) + ml_scores.get("admiration", 0))
    fear_dom = (ml_scores.get("fear", 0) + ml_scores.get("anger", 0))
    if joy_dom or fear_dom:
        return ("emotion_direction", "comforting" if joy_dom >= fear_dom else "intense")
    return None

GENRE_LABELS_CACHE: Dict[str, str] = {}
GENRE_FORMS_CACHE: Dict[str, str] = {}
GENRE_SYNONYMS_CACHE: Dict[str, str] = {}
ONTO_BASE = "http://www.semanticweb.org/ibrah/ontologies/2025/11/emotion-ontology#"

def _normalize_simple(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())

def _camel_to_words(name: str) -> str:
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    return re.sub(r"[^a-zA-Z0-9 ]", " ", s).strip()

def _load_genre_labels() -> None:
    global GENRE_LABELS_CACHE, GENRE_FORMS_CACHE
    if GENRE_LABELS_CACHE:
        return
    try:
        with open("kg/data/genre_labels.ttl", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                m = re.search(r"emo:(\w+)\s+rdfs:label\s+\"([^\"]+)\"", line)
                if m:
                    curie = f"emo:{m.group(1)}"
                    label = m.group(2)
                    GENRE_LABELS_CACHE[curie] = label
                    GENRE_FORMS_CACHE[curie] = _normalize_simple(label)
    except Exception:
        GENRE_LABELS_CACHE["emo:Comedy"] = "Comedy"
        GENRE_LABELS_CACHE["emo:Drama"] = "Drama"
        GENRE_LABELS_CACHE["emo:Horror"] = "Horror"
        GENRE_LABELS_CACHE["emo:Action"] = "Action"
        GENRE_LABELS_CACHE["emo:Family"] = "Family"
        GENRE_FORMS_CACHE = {k: _normalize_simple(v) for k, v in GENRE_LABELS_CACHE.items()}

SLOT_ORDER = [
    "emotion_direction",
    "desired_outcome",
    "pace_preference",
    "violence_tolerance",
    "era_preference",
    "content_sensitivity",
]

def _load_genre_synonyms() -> None:
    global GENRE_SYNONYMS_CACHE
    if GENRE_SYNONYMS_CACHE:
        return
    try:
        with open("kg/data/genre_synonyms.json", "r", encoding="utf-8") as f:
            import json as _json
            data = _json.load(f)
            for curie, syn in data.items():
                if isinstance(syn, list) and syn:
                    GENRE_SYNONYMS_CACHE[curie] = syn[0]
    except Exception:
        GENRE_SYNONYMS_CACHE = {}

def interpret_followup_answer(pending_id: str, user_text: str, ml_scores: Dict[str, float]) -> Optional[str]:
    t = _normalize_text(user_text)
    synonyms = {
        "emotion_direction": {
            "comforting": [
                "comfort", "comforting", "light", "happy", "calm", "gentle",
                "soothing", "feel better", "uplifting", "positive", "warm",
                "heartwarming", "wholesome"
            ],
            "intense": [
                "intense", "dark", "thrill", "thrilling", "scary", "horror",
                "action", "sad", "dramatic", "serious", "heavy"
            ],
        },
        "desired_outcome": {
            "feel_better": ["feel better", "lift mood", "uplift", "cheer up"],
            "process_feelings": ["process feelings", "reflect", "think", "ponder"],
            "get_excited": ["get excited", "pump", "adrenaline", "thrill"],
        },
        "era_preference": {
            "classic": ["classic", "older", "vintage", "retro"],
            "modern": ["modern", "newer", "recent", "contemporary"],
        },
        "content_sensitivity": {
            "avoid_horror": ["avoid horror", "no horror", "not horror"],
            "avoid_drama": ["avoid drama", "no drama", "not drama", "heavy"],
            "avoid_violence": ["avoid violence", "no violence", "not violent", "no action"],
            "none": ["either", "no preference", "anything", "tell me", "idk", "dont know"]
        },
        "intensity_style": {
            "adrenaline": ["adrenaline", "adrenaline pumping", "pump", "exciting", "high octane"],
            "suspense": ["suspense", "tense", "edge of seat", "thriller"],
            "dark": ["dark", "edgy", "grisly", "grim", "horror"],
        },
        "comfort_style": {
            "uplifting": ["uplifting", "feel good", "cheer up", "positive"],
            "heartwarming": ["heartwarming", "warm", "wholesome"],
            "calm": ["calm", "soothing", "relaxing", "low stakes", "calming", "gentle"],
            "none": ["either", "no preference", "anything", "tell me", "idk", "dont know"]
        },
        "pace_preference": {
            "fast": ["fast", "fast paced", "quick", "rapid"],
            "slow": ["slow", "slow burn", "steady"],
            "none": ["either", "no preference", "anything", "tell me", "idk", "dont know"]
        },
        "violence_tolerance": {
            "none": ["no violence", "avoid violence"],
            "mild": ["mild", "some", "a little"],
            "strong": ["strong", "high", "ok with violence"],
            "none_opt": ["either", "no preference", "anything", "tell me", "idk", "dont know"]
        }
    }
    opts = synonyms.get(pending_id)
    if not opts:
        return None
    for value, words in opts.items():
        for w in words:
            if w in t:
                if pending_id in {"emotion_direction", "desired_outcome"}:
                    return f"emo:{value}"
                return value
    return None

# --- External movie details (TMDb) ---
from typing import Any

TMDB_API_KEY = (os.getenv("TMDB_API_KEY") or "").strip()
TMDB_IMG_BASE = "https://image.tmdb.org/t/p/w500"
MOVIE_DETAILS_CACHE: Dict[str, Dict[str, Any]] = {}

class MovieDetailsRequest(BaseModel):
    title: str
    year: Optional[str] = None

class MovieDetailsResponse(BaseModel):
    found: bool
    details: Optional[Dict[str, Any]]


def _fetch_tmdb_details(title: str, year: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if not TMDB_API_KEY:
        logger.warning("TMDB_API_KEY not set; skipping external lookup")
        return None
    cache_key = f"{title}|{year or ''}".strip()
    if cache_key in MOVIE_DETAILS_CACHE:
        return MOVIE_DETAILS_CACHE[cache_key]

    def _norm(s: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()

    def _parse_year(y: Optional[str]) -> Optional[int]:
        if y is None:
            return None
        m = re.search(r"\b(19|20)\d{2}\b", str(y))
        if m:
            try:
                return int(m.group(0))
            except Exception:
                pass
        try:
            return int(float(str(y)))
        except Exception:
            return None

    try:
        y = _parse_year(year)
        params = {
            "api_key": TMDB_API_KEY,
            "query": title,
            "include_adult": "false",
            "language": "en-US",
        }
        if y:
            params["year"] = y
        r = requests.get("https://api.themoviedb.org/3/search/movie", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        if not results:
            return None
        nt = _norm(title)
        # score candidates by exact/partial title match, year match, and vote_count as tie-breaker
        scored = []
        for mres in results:
            rel_year = (mres.get("release_date") or "")[:4]
            tf = [mres.get("title") or "", mres.get("original_title") or ""]
            score = 0.0
            if any(_norm(t) == nt for t in tf):
                score += 3.0
            elif any(nt and (nt in _norm(t)) for t in tf):
                score += 1.0
            if y and rel_year == str(y):
                score += 2.0
            try:
                score += (float(mres.get("vote_count", 0)) / 10000.0)
            except Exception:
                pass
            scored.append((score, mres))
        scored.sort(key=lambda x: x[0], reverse=True)
        match = scored[0][1] if scored else None
        if not match:
            return None
        movie_id = match.get("id")
        dresp = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}",
            params={"api_key": TMDB_API_KEY, "append_to_response": "credits"},
            timeout=10,
        )
        dresp.raise_for_status()
        d = dresp.json()
        details = {
            "title": d.get("title") or match.get("title"),
            "year": (d.get("release_date") or match.get("release_date") or "")[:4],
            "rating": d.get("vote_average"),
            "genres": [g.get("name") for g in d.get("genres", [])],
            "cast": [c.get("name") for c in d.get("credits", {}).get("cast", [])[:8]],
            "overview": d.get("overview"),
            "poster_url": (TMDB_IMG_BASE + d["poster_path"]) if d.get("poster_path") else None,
            "tmdb_id": movie_id,
            "source": "tmdb",
        }
        MOVIE_DETAILS_CACHE[cache_key] = details
        return details
    except Exception as e:
        logger.error(f"TMDb details fetch failed: {e}")
        return None


@app.post("/movie/details", response_model=MovieDetailsResponse)
def movie_details(req: MovieDetailsRequest) -> MovieDetailsResponse:
    if not req.title or not req.title.strip():
        raise HTTPException(status_code=400, detail="Title required")
    details = _fetch_tmdb_details(req.title.strip(), req.year)
    return MovieDetailsResponse(found=bool(details), details=details)


