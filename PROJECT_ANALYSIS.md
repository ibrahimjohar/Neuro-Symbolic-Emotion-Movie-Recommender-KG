# Neuro-Symbolic Emotion Movie Recommender - Project Analysis

## Project Overview
A neuro-symbolic emotion-aware movie recommendation system that combines:
- **Deep Learning (DL)**: Emotion classification using GoEmotions model
- **Knowledge Graph (KG)**: OWL ontology with SWRL rules for emotion-to-genre reasoning
- **SPARQL**: Querying Apache Jena Fuseki for movie recommendations

## Folder Structure Analysis

### `/api` - FastAPI REST API
- **`main.py`**: Main API endpoints (`/analyze`, `/chat`)
  - **Issue**: SPARQL query in `/chat` endpoint is built but never executed
  - Uses `fetch_movies_for_genres()` which works, but the new SPARQL query (lines 215-243) is only printed for debugging
- **`sparql_client.py`**: Client for Jena Fuseki SPARQL endpoint
  - Endpoint: `http://localhost:3030/emotion/sparql`

### `/dl` - Deep Learning Module
- **`emotion_inference.py`**: Loads GoEmotions model and infers emotions from text
  - Model path: `models/emotion_classifier/`
  - Returns: `{emotion_label: confidence_score}`
- **`dataset_loader.py`**: Loads GoEmotions dataset labels
- **`train_model.py`**: Training script for emotion classifier
- **`preprocess.py`**: Data preprocessing utilities

### `/nlp` - NLP Processing
- **`emotion_dominance.py`**: Selects top-k dominant emotions using softmax
- **`emotion_mapper.py`**: Maps ML labels → ontology individuals → genre URIs
  - `EMOTION_TO_ONTOLOGY`: Maps "joy" → "joy_1"
  - `ONTOLOGY_EMOTION_TO_GENRES`: Maps "joy_1" → ["emo:comedy_genre", "emo:family_genre"]

### `/kg` - Knowledge Graph
- **`emotion_ontology.rdf`**: Main OWL ontology
  - Classes: `TextualInput`, `EmotionalState`, `MovieGenre`, `Movie`
  - Properties: `expressesEmotion`, `suggestsGenre`, `belongsToGenre`
  - SWRL rules for emotion-to-genre inference
- **`emotion-inferred.ttl`**: Inferred triples from SWRL rules
- **`emotion-materialized.ttl`**: Materialized inferences
- **`movies/`**: Movie data and schema
  - `movies_schema.ttl`: Movie ontology schema
  - `movies_data.ttl`: Movie instances (empty or minimal)

### `/reasoning/jena` - Apache Jena Configuration
- **`fuseki/config.ttl`**: Fuseki server configuration
  - Dataset: `/emotion`
  - TDB2 location: `data/`
- **`sparql_queries.py`**: Example SPARQL queries (not used in API)

### `/data` - Data Files
- **`movie_kb_final.csv`**: Processed movie knowledge base
- **`movies_kb_raw.csv`**: Raw movie data
- **`raw/ml-25m.zip`**: MovieLens dataset

### `/models` - Trained Models
- **`emotion_classifier/`**: Fine-tuned GoEmotions model
  - Contains: `config.json`, `model.safetensors`, tokenizer files

### `/docker` - Docker Configuration
- **`docker-compose.yml`**: Orchestrates Fuseki + API containers
- **`Dockerfile`**: Python API container definition

### `/notebooks` - Jupyter Notebooks
- Exploration and data preparation notebooks
- `05_movies_to_rdf.py`: Converts movies to RDF

### `/ui` - User Interface
- Currently empty

## SPARQL Query Issue in `/chat` Endpoint

### Problem Location
`api/main.py`, lines 215-243

### Issues Identified

1. **Query Not Executed**
   - The SPARQL query is built (line 215) and printed (line 244) but never executed
   - Code continues to use `fetch_movies_for_genres()` (line 255) instead
   - The query results are never used

2. **Incorrect VALUES Block Format**
   ```python
   values_block = " ".join(ontology_inds)  # Line 213
   ```
   - `ontology_inds` contains strings like `["joy_1", "fear_1"]`
   - Should be formatted as: `emo:joy_1 emo:fear_1` or `<http://...> <http://...>`
   - Current format produces invalid SPARQL: `VALUES ?emotionInd { joy_1 fear_1 }`

3. **Hardcoded Individual Reference**
   - Query references `emo:text_test` (lines 227-228)
   - This is a hardcoded individual that may not exist for each request
   - Should use a dynamic text individual or query differently

4. **Query Logic Assumptions**
   - Assumes `?emotionInd emo:suggestsGenre ?genreInd` (line 231)
   - But emotion individuals may not have direct `suggestsGenre` properties
   - The relationship might be inferred through SWRL rules via `TextualInput` individuals

5. **Missing FastAPI Dependencies**
   - `requirements.txt` doesn't include `fastapi` and `uvicorn`

### Current Working Flow (in `/analyze` endpoint)
1. ML inference → emotion scores
2. Map emotions → genre URIs (via `ONTOLOGY_EMOTION_TO_GENRES`)
3. Query movies using `build_movies_query_for_genres()` (works correctly)
4. Returns movies filtered by genre URIs

### Intended Flow (in `/chat` endpoint - not working)
1. ML inference → emotion scores
2. Select dominant emotions
3. Map to ontology individuals
4. **Query KG using emotion individuals** (this part is broken)
5. Use SWRL-inferred relationships to find genres
6. Return movies

## Architecture Flow

```
User Text Input
    ↓
[DL Module] → GoEmotions Model → {emotion: score}
    ↓
[NLP Module] → Select Dominant Emotions
    ↓
[Mapper] → Map to Ontology Individuals (e.g., "joy_1")
    ↓
[SPARQL Query] → Query Jena Fuseki KG
    ↓
[SWRL Rules] → Infer Genres from Emotions
    ↓
[Movie Query] → Find Movies by Genre
    ↓
Return Recommendations
```

## Dependencies

### Missing from `requirements.txt`:
- `fastapi`
- `uvicorn`
- `pydantic` (already present)

### Present:
- `transformers`, `torch` (for DL)
- `requests` (for SPARQL client)
- `spacy`, `nltk` (for NLP)
- `pandas`, `numpy` (for data processing)

## Recommendations

1. **Fix SPARQL Query Execution**: Actually execute the query and use results
2. **Fix VALUES Block**: Format ontology individuals as proper URIs
3. **Dynamic Text Individuals**: Create/use text individuals per request or query differently
4. **Verify KG Structure**: Ensure emotion individuals have expected relationships
5. **Add Missing Dependencies**: Add FastAPI and uvicorn to requirements.txt
6. **Error Handling**: Add proper error handling for SPARQL queries
7. **Unify Approaches**: Decide whether to use direct genre mapping (working) or KG reasoning (intended)

## Working Components
✅ ML emotion inference
✅ Emotion dominance selection
✅ Genre mapping (direct approach)
✅ Movie querying by genre URIs
✅ `/analyze` endpoint
✅ SPARQL client connection

## Non-Working Components
❌ SPARQL query execution in `/chat` endpoint
❌ Emotion-to-genre reasoning via KG (query built but not used)
❌ Dynamic text individual creation/querying

