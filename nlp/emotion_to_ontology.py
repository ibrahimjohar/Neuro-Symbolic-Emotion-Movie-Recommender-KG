"""
maps ML-predicted emotions to ontology emotion individuals.
used as the bridge between ML and symbolic reasoning.
"""

# nlp/emotion_to_ontology.py

ONTOLOGY_EMOTION_MAP = {
    #cognitive / reflective
    "confusion": "confusion_1",
    "curiosity": "curiosity_1",
    "realization": "reflective_1",

    #negative
    "fear": "fear_1",
    "sadness": "sadness_1",
    "grief": "grief_1",
    "disgust": "distressed_1",
    "anger": "distressed_1",
    "disappointment": "distressed_1",
    "remorse": "distressed_1",

    #positive
    "joy": "joy_1",
    "love": "love_1",
    "excitement": "excitement_1",
    "optimism": "uplifting_1",
    "gratitude": "uplifting_1",
    "relief": "uplifting_1",
}

THRESHOLD = 0.4  #industry-reasonable for GoEmotions multi-label

def emotions_to_ontology(scores: dict) -> list[str]:
    mapped = set()

    for emo, score in scores.items():
        if score >= THRESHOLD and emo in ONTOLOGY_EMOTION_MAP:
            mapped.add(ONTOLOGY_EMOTION_MAP[emo])

    return list(mapped)
