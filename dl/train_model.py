"""
training pipeline for emotion classification.
this module:
- loads the GoEmotions dataset
- preprocesses text and labels
- fine-tunes a pretrained transformer model
the trained model predicts emotion probabilities for input text.
"""
import torch
from torch.utils.data import DataLoader

from transformers import AutoModelForSequenceClassification
from torch.optim import AdamW

from dl.dataset_loader import load_goemotions
from dl.preprocess import tokenize_texts, binarize_labels
from dl.preprocess import tokenizer

"""
torch → tensors + training
DataLoader → feeds data in batches
AutoModelForSequenceClassification → ready-made classifier head
AdamW → optimizer (industry standard)
imports from our own files → modular design
"""

#initilialize model
MODEL_NAME = "distilroberta-base"

def load_model(num_labels):
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=num_labels,
        problem_type = "multi_label_classification"
    )
    return model

"""
we're telling the model:
-> “you’ll predict 28 emotions”
-> “multiple emotions can be true at once”
this automatically:
-> uses sigmoid activation
-> uses binary cross-entropy loss internally
"""

#preparing a small training batch
def prepare_batch(batch, label_names):
    texts = batch["text"]
    labels = [
        binarize_labels(label_ids, num_labels=len(label_names))
        for label_ids in batch["labels"]
    ]
    
    tokens = tokenize_texts(texts)
    labels = torch.stack(labels)
    
    return {
        "input_ids": tokens["input_ids"],
        "attention_mask": tokens["attention_mask"],
        "labels": labels
    }

"""
for a batch of examples:
1. extract raw text
2. convert emotion labels → binary vectors
3. tokenize text → numbers

bundle everything together

model receives: (text as numbers, correct emotions)
"""

def collate_fn(batch):
    """
    Custom collation function to handle variable-length text.
    The batch is passed as a list of dataset samples.
    """
    return {
        "text": [item["text"] for item in batch],
        "labels": [item["labels"] for item in batch],
    }


#minimal training loop
def train():
    dataset, label_names = load_goemotions()
    model = load_model(num_labels=len(label_names))
    
    model.train()
    
    optimizer = AdamW(model.parameters(), lr=5e-5)
    
    train_data = dataset["train"].select(range(64)) #small subset for learning
    dataloader = DataLoader(train_data, batch_size=8, shuffle=True, collate_fn=collate_fn)
    
    for epoch in range(1):
        for batch in dataloader:
            inputs = prepare_batch(batch, label_names)
            
            outputs = model(**inputs)
            loss = outputs.loss
            
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            
            print(f"loss: {loss.item():.4f}")
    
        save_path = "models/emotion_classifier"
        model.save_pretrained(save_path)
        tokenizer.save_pretrained(save_path)
        print(f"Model and tokenizer saved to {save_path}")

            

"""
each iteration:
1. model makes predictions
2. compares with true emotions
3. computes “how wrong it was” (loss)
4. nudges itself to be less wrong next time

that's learning.

we're:
- using a tiny subset
- running only 1 epoch
printing loss so you see learning happen
"""

if __name__ == "__main__":
    train()
    
#output:
"""loss: 0.6819
loss: 0.6629
loss: 0.6402
loss: 0.6079
loss: 0.5806
loss: 0.5362
loss: 0.5146
loss: 0.4705"""