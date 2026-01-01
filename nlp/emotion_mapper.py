from typing import Dict, List

# --- Map ML label -> ontology individual (exact individual names you used in Protégé/Jena) ---
EMOTION_TO_ONTOLOGY: Dict[str, str] = {
    "admiration": "admiration_1",
    "amusement": "amusement_1",
    "anger": "anger_1",
    "annoyance": "annoyance_1",
    "approval": "approval_1",
    "caring": "caring_1",
    "confusion": "confusion_1",
    "curiosity": "curiosity_1",
    "desire": "desire_1",
    "disappointment": "disappointment_1",
    "disgust": "disgust_1",
    "embarrassment": "embarrassment_1",
    "excitement": "excitement_1",
    "fear": "fear_1",
    "gratitude": "gratitude_1",
    "grief": "grief_1",
    "joy": "joy_1",
    "love": "love_1",
    "nervousness": "nervousness_1",
    "optimism": "optimism_1",
    "pride": "pride_1",
    "realization": "realization_1",
    "relief": "relief_1",
    "remorse": "remorse_1",
    "sadness": "sadness_1",
    "surprise": "surprise_1",
    "neutral": "neutral_1",
    # add any other labels you use — keep lowercase keys matching ML output
}

# --- Map ontology emotion individual -> ontology genre URIs (used by SPARQL filter) ---
ONTOLOGY_EMOTION_TO_GENRES: Dict[str, List[str]] = {
    "joy_1": ["emo:comedy_genre", "emo:family_genre"],
    "amusement_1": ["emo:comedy_genre"],
    "anger_1": ["emo:crime_genre", "emo:thriller_genre"],
    "confusion_1": ["emo:mystery_genre"],
    "curiosity_1": ["emo:mystery_genre", "emo:fantasy_genre"],
    "fear_1": ["emo:horror_genre", "emo:thriller_genre"],
    "excitement_1": ["emo:action_genre", "emo:adventure_genre"],
    "sadness_1": ["emo:drama_genre"],
    "grief_1": ["emo:drama_genre"],
    "love_1": ["emo:romance_genre"],
    "neutral_1": ["emo:documentary_genre"],
    # continue for all your emotion individuals...
}

# --- Helpers ---
def map_ml_to_ontology_individuals(emotions: List[str]) -> List[str]:
    """Given ML labels (lowercase), return ontology individual names (e.g., 'confusion_1')."""
    return [EMOTION_TO_ONTOLOGY[e] for e in emotions if e in EMOTION_TO_ONTOLOGY]

def map_ontology_individuals_to_genres(individuals: List[str]) -> List[str]:
    """Given ontology individuals, return a unique list of genre URIs (e.g., 'emo:comedy_genre')."""
    out = []
    for ind in individuals:
        out.extend(ONTOLOGY_EMOTION_TO_GENRES.get(ind, []))
    # preserve order but dedupe
    return list(dict.fromkeys(out))