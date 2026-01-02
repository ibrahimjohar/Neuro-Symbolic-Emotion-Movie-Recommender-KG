from collections import defaultdict

DECAY = 0.8

SESSIONS = {}

def update_session(session_id: str, ml_scores: dict) -> dict:
    if session_id not in SESSIONS:
        SESSIONS[session_id] = defaultdict(float)

    session = SESSIONS[session_id]

    for emo in list(session.keys()):
        session[emo] *= DECAY

    for emo, score in ml_scores.items():
        session[emo] += score

    return dict(session)

def dominant_emotions(session_scores: dict, k: int = 3):
    return sorted(session_scores.items(), key=lambda x: x[1], reverse=True)[:k]