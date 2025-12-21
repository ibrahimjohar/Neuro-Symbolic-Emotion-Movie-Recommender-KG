import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from dl.dataset_loader import load_goemotions

MODELS_PATH = "models/emotion_classifier"

def load_model_and_tokenizer():
    model = AutoModelForSequenceClassification.from_pretrained(MODELS_PATH)
    tokenizer = AutoTokenizer.from_pretrained(MODELS_PATH)
    model.eval()
    return model, tokenizer

def predict_emotions(text, threshold=0.3):
    dataset, label_names = load_goemotions()
    model, tokenizer = load_model_and_tokenizer()
    
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
    
    predictions = {
        label_names[i]: float(probs[i])
        for i in range(len(label_names))
        if probs[i] >= threshold
    }
    
    return predictions


if __name__ == "__main__":
    text = "This movie was slow but emotionally powerful and thought-provoking."
    emotions = predict_emotions(text)

    print("input text: ")
    print(text)
    print("\npredicted emotions: ")
    for emo, score in emotions.items():
        print(f"{emo}: {score:.3f}")