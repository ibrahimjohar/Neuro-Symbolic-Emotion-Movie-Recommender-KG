from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Emotion-Aware Movie Recommender API")

class HealthResponse(BaseModel):
    status: str

@app.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok"}