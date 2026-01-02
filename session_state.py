from collections import defaultdict
from typing import Dict

#in-memory session store
_SESSIONS = {}

CONFIDENCE_INCREMENT = 0.2
CONFIDENCE_THRESHOLD = 0.6

def get_session(session_id: str):
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = {
            "emotions": defaultdict(list),   # emotion -> [scores]
            "preferences": {},               # future extension
            "confidence": 0.0
        }
    return _SESSIONS[session_id]

def update_emotions(session_id: str, emotion_scores: dict):
    session = get_session(session_id)

    for emo, score in emotion_scores.items():
        session["emotions"][emo].append(score)

    session["confidence"] = min(
        1.0,
        session["confidence"] + CONFIDENCE_INCREMENT
    )

    return session

def aggregated_emotions(session_id: str):
    session = get_session(session_id)

    aggregated = {}
    for emo, scores in session["emotions"].items():
        aggregated[emo] = sum(scores) / len(scores)

    return aggregated

def is_confident_enough(session_id: str) -> bool:
    return get_session(session_id)["confidence"] >= CONFIDENCE_THRESHOLD

class ConversationContext:
    def __init__(self):
        self.emotion_scores: Dict[str, float] = defaultdict(float)
        self.turns: int = 0

    def update(self, new_scores: Dict[str, float]):
        for emo, score in new_scores.items():
            self.emotion_scores[emo] += score
        self.turns += 1

    def dominant(self, top_k=3):
        return sorted(
            self.emotion_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]

    def confidence(self):
        if not self.emotion_scores:
            return 0.0
        return max(self.emotion_scores.values())

_CONTEXTS = {}

def get_context(session_id: str) -> ConversationContext:
    if session_id not in _CONTEXTS:
        _CONTEXTS[session_id] = ConversationContext()
    return _CONTEXTS[session_id]
