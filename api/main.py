from fastapi import FastAPI
from pydantic import BaseModel
from api.sparql_client import run_query

app = FastAPI(title="Emotion-Aware Movie Recommender API")

class HealthResponse(BaseModel):
    status: str

@app.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok"}

@app.get("/recommend")
def recommend(text_id: str):
    query = f"""
    PREFIX emo: <http://www.semanticweb.org/ibrah/ontologies/2025/11/emotion-ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT DISTINCT ?title ?genreLabel
    WHERE {{
        emo:{text_id} emo:suggestsGenre ?gInd .
        ?gInd rdf:type ?gClass .
        ?gClass rdfs:label ?genreLabel .
        ?movie a emo:Movie ;
            emo:title ?title ;
            emo:belongsToGenre ?gClass .
    }}
    LIMIT 20
    """
    return run_query(query)