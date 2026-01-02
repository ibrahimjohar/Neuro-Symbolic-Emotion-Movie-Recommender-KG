from typing import Dict, List

# --- Map ML label -> ontology individual (exact individual names you used in Protégé/Jena) ---
EMOTION_TO_ONTOLOGY: Dict[str, str] = {
    "admiration": "emo:admiration_1",
    "amusement": "emo:amusement_1",
    "anger": "emo:anger_1",
    "annoyance": "emo:annoyance_1",
    "approval": "emo:approval_1",
    "caring": "emo:caring_1",
    "confusion": "emo:confusion_1",
    "curiosity": "emo:curiosity_1",
    "desire": "emo:desire_1",
    "disappointment": "emo:disappointment_1",
    "disgust": "emo:disgust_1",
    "embarrassment": "emo:embarrassment_1",
    "excitement": "emo:excitement_1",
    "fear": "emo:fear_1",
    "gratitude": "emo:gratitude_1",
    "grief": "emo:grief_1",
    "joy": "emo:joy_1",
    "love": "emo:love_1",
    "nervousness": "emo:nervousness_1",
    "optimism": "emo:optimism_1",
    "pride": "emo:pride_1",
    "realization": "emo:realization_1",
    "relief": "emo:relief_1",
    "remorse": "emo:remorse_1",
    "sadness": "emo:sadness_1",
    "surprise": "emo:surprise_1",
    "neutral": "emo:neutral_1",
    # add any other labels you use — keep lowercase keys matching ML output
}

def map_ml_to_ontology_individuals(emotion_names):
    return [EMOTION_TO_ONTOLOGY[e] for e in emotion_names if e in EMOTION_TO_ONTOLOGY]