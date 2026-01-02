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

# --- Helpers ---
def map_ml_to_ontology_individuals(emotions: List[str]) -> List[str]:
    """Given ML labels (lowercase), return ontology individual names (e.g., 'confusion_1')."""
    return [EMOTION_TO_ONTOLOGY[e] for e in emotions if e in EMOTION_TO_ONTOLOGY]