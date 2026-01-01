from dl.emotion_inference import infer_emotions
from nlp.emotion_to_ontology import emotions_to_ontology

text = "The movie was intense, unsettling, but deeply thought-provoking."

scores = infer_emotions(text)
mapped = emotions_to_ontology(scores)

print("ML scores:", scores)
print("Ontology emotions:", mapped)