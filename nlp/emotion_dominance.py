import torch
import math

def softmax(scores: dict) -> dict:
    """
    Convert raw emotion scores into a probability distribution.
    """
    values = torch.tensor(list(scores.values()), dtype=torch.float32)
    probs = torch.softmax(values, dim=0)

    return {
        emo: float(probs[i])
        for i, emo in enumerate(scores.keys())
    }


def select_dominant_emotions(
    scores: dict,
    top_k: int = 2,
    min_prob: float = 0.15
) -> list[str]:
    """
    Select top-k dominant emotions after softmax.
    """

    probs = softmax(scores)

    #sort emotions by probability
    ranked = sorted(
        probs.items(),
        key=lambda x: x[1],
        reverse=True
    )

    #take top-k, but ignore very weak signals
    dominant = [
        emo for emo, p in ranked[:top_k]
        if p >= min_prob
    ]

    return dominant

if __name__ == "__main__":
    test_scores = {
        "joy": 0.33,
        "fear": 0.43,
        "curiosity": 0.42,
        "sadness": 0.31,
        "love": 0.39
    }

    dominant = select_dominant_emotions(test_scores, top_k=2)
    print(dominant)