"""
maps ML-predicted emotions to ontology emotion individuals.
used as the bridge between ML and symbolic reasoning.
"""

DEFAULT_THRESHOLD = 0.5

#ML label → ontology emotion INDIVIDUAL
EMOTION_TO_ONTOLOGY = {
    #cognitive
    "confusion": "confusion_1",
    "curiosity": "curiosity_1",
    "realization": "realization_1",

    #positive
    "joy": "joy_1",
    "love": "love_1",
    "excitement": "excitement_1",
    "optimism": "optimism_1",
    "admiration": "admiration_1",

    #negative
    "fear": "fear_1",
    "grief": "grief_1",
    "sadness": "sadness_1",
    "anger": "anger_1",
    "disgust": "disgust_1",
    "disappointment": "disappointment_1",

    #reflective / Uplifting
    "surprise": "reflective_1",
    "gratitude": "uplifting_1",
    "relief": "uplifting_1",

    #neutral (kept but usually ignored by rules)
    "neutral": "neutral_1"
}


def emotions_to_ontology(
    emotion_scores: dict,
    threshold: float = DEFAULT_THRESHOLD
) -> list[str]:
    """
    convert ML emotion predictions into ontology emotion individuals.
    Input:
        emotion_scores = { "joy": 0.42, "fear": 0.31, ... }
    Output:
        [ "joy_1", "curiosity_1", "fear_1" ]
    """

    ontology_emotions = []

    for emotion, score in emotion_scores.items():
        if score < threshold:
            continue

        if emotion not in EMOTION_TO_ONTOLOGY:
            continue

        ontology_emotions.append(EMOTION_TO_ONTOLOGY[emotion])

    #remove duplicates while preserving order
    seen = set()
    return [e for e in ontology_emotions if not (e in seen or seen.add(e))]
