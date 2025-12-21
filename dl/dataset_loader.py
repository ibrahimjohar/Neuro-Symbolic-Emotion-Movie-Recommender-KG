#loading the GoEmotions dataset cleanly and consistently and expose it to the rest of the system
#no preprocessing, no tokenization, and no training here.

"""
dataset loading utilities for the emotion-aware recommender system.

this module is responsible for:
- loading the GoEmotions dataset
- exposing train/validation/test splits
- providing access to emotion label names

no preprocessing or model logic is included here.
"""
from datasets import load_dataset

"""
    load the GoEmotions dataset.
    -> returns:
    dataset : datasets.DatasetDict
        a dictionary-like object with keys:
        - 'train'
        - 'validation'
        - 'test'
    label_names : list[str]
        list of emotion label names indexed by label ID.
    """

def load_goemotions():
    dataset = load_dataset("go_emotions")
    label_names = dataset["train"].features["labels"].feature.names
    return dataset, label_names

if __name__ == "__main__":
    ds, labels = load_goemotions()
    print("splits: ", ds.keys())
    print("num of labels: ", len(labels))
    print("first label: ", labels[0])