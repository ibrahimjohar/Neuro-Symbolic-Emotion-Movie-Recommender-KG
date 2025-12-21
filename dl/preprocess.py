#creating a reusable preprocessing module that
# - converts raw GoEmotions labels into a multi-label binary format
# - tokenizes text using the same tokenizer as the model
# - outputs data in a format that pytorch + transformers can consume

"""
GoEmotions is:
- multi-label (one text → many emotions)
- annotated with label indices, not names
Transformers expect:
- fixed-size numerical input (input_ids, attention_mask)
- labels as binary vectors for multi-label classification
this step performs the mathematical alignment between:
    human language → neural model inputs
"""

"""
preprocessing utilities for emotion classification.
this module handles:
- multi-label binarization of GoEmotions labels
- tokenization of input text using a transformer tokenizer
doesnt include:
- model training
- evaluation
- inference logic
"""

from transformers import AutoTokenizer
import torch

TOKENIZER_NAME = "distilroberta-base"

tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)

#mutli-label binarization function
def binarize_labels(label_ids, num_labels):
    """
    convert a list of label indices into a multi-hot binary vector.
    parameters:
    ----------
    label_ids : list[int]
        list of emotion label indices.
    num_labels : int
        total number of emotion labels.
    returns:
    -------
    torch.Tensor
        binary tensor of shape (num_labels,)
    """
    
    vector = torch.zeros(num_labels)
    for idx in label_ids:
        vector[idx] = 1.0
    return vector

#GoEmotions is multi-label
#binary vector + sigmoid loss = correct formulation
#this function is reusable everywhere

def tokenize_texts(texts, max_length=128):
    """
    tokenize a list of texts using the transformer tokenizer.
    parameters:
    ----------
    texts : list[str]
        input text samples.
    max_length : int
        maximum sequence length.
    returns:
    -------
    dict
        dictionary containing input_ids and attention_mask tensors.
    """
    
    return tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors = "pt"
    )
    
if __name__ == "__main__":
    sample_texts = [
        "this movie made me feel uneasy and thoughtful.",
        "i absolutely loved the cinematography!"
    ]

    tokens = tokenize_texts(sample_texts)
    print(tokens.keys())
    print(tokens["input_ids"].shape)