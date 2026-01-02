from collections import defaultdict
from typing import Dict

#in-memory session store
_SESSIONS = {}

_SESSIONS.clear()

def update_emotions(session_id: str, ml_scores: dict):
    session = get_session(session_id)

    if "confidence" not in session:
        session["confidence"] = 0.0

CONFIDENCE_INCREMENT = 0.2
CONFIDENCE_THRESHOLD = 0.6

def get_session(session_id: str):
    session = _SESSIONS.setdefault(
        session_id,
        {
            "emotions": {},
            "turns": 0,
            "confidence": 0.0,
        }
    )

    if "confidence" not in session:
        session["confidence"] = 0.0

    return session

def _get_session(session_id):
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = {
            "emotions": {},
            "turns": 0,
            "pending_question": None
        }
    return _SESSIONS[session_id]

def set_pending_question(session_id, question_id):
    session = _get_session(session_id)
    session["pending_question"] = question_id


def get_pending_question(session_id):
    session = _get_session(session_id)
    return session.get("pending_question")


def clear_pending_question(session_id):
    session = _get_session(session_id)
    session["pending_question"] = None


def update_emotions(session_id: str, ml_scores: dict):
    session = _SESSIONS.setdefault(
        session_id,
        {
            "emotions": {},
            "turns": 0,
            "confidence": 0.0
        }
    )

    for emo, score in ml_scores.items():
        if emo not in session["emotions"]:
            session["emotions"][emo] = []

        session["emotions"][emo].append(score)

    session["turns"] += 1
    
    session["confidence"] = max(session["confidence"], max(ml_scores.values(), default=0.0))

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
