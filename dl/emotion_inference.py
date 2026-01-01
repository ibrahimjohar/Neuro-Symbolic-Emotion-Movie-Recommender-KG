import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from dl.dataset_loader import load_goemotions

MODEL_PATH = "models/emotion_classifier"

#LOAD ONCE (IMPORTANT FOR API USE) ----
dataset, LABEL_NAMES = load_goemotions()
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model.eval()


def infer_emotions(text: str) -> dict:
    """
    Input: raw user text
    Output: { emotion_label: confidence }
    """

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Input text must be non-empty")

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=128
    )

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits

    probs = torch.sigmoid(logits)[0]

    return {
        LABEL_NAMES[i]: round(float(probs[i]), 4)
        for i in range(len(LABEL_NAMES))
    }
    
if __name__ == "__main__":
    text = "This movie was slow but emotionally powerful and thought-provoking."
    emotions = infer_emotions(text)
    print(emotions)