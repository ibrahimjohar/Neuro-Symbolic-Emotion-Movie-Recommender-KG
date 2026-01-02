# Neuro‑Symbolic Emotion Movie Recommender (Quickstart)

This project recommends movies based on how you feel using a neuro‑symbolic approach: an ML emotion classifier plus a semantic knowledge graph queried with SPARQL.

## Prerequisites
- Python 3.10+ (Windows PowerShell recommended)
- Node.js 18+ and npm
- Apache Jena Fuseki (standalone) for SPARQL
- Optional: Docker Desktop (alternative way to run Fuseki)

## 1) Enter the project
```powershell
cd "c:\Ibrahim\Personal\University Stuff\Knowledge Representation & Reasoning\KRR Project\Neuro-Symbolic-Emotion-Movie-Recommender-KG"
```

## 2) Python backend setup
Choose either virtualenv (recommended) or install directly without a venv.

- Option A: Use a virtualenv (recommended)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```
To exit the environment later: `deactivate`.

- Option B: Skip virtualenv (install globally or per user)
```powershell
# Install to your user site-packages to avoid admin rights
python -m pip install --user --upgrade pip
python -m pip install --user -r requirements.txt
```
Notes:
- Skipping venv is fine if you prefer, but be aware it installs packages to your global/user Python and may affect other projects.
- If you have multiple Python versions, use `py -3.10 -m pip` instead of `python -m pip` to target Python 3.10 explicitly.

## 3) Start the SPARQL endpoint (Apache Jena Fuseki — no Docker)
Docker isn’t required. On Windows, install and run Fuseki standalone:

1) Download Fuseki from the Apache Jena website and unzip.
2) Start the server:
```powershell
# From the Fuseki folder
fuseki-server.bat
# Server UI: http://localhost:3030/
```
3) Create a dataset via the admin UI:
- Open `http://localhost:3030/` → “Manage datasets” → “Add new dataset”.
- Name the dataset (e.g., `movies`), type `TDB2`, then create.
4) Load the knowledge graph:
- In the dataset page, upload TTL/RDF files from `kg/`, at minimum:
  - `kg/emotion_ontology.rdf`
  - `kg/movies.ttl`
- You can also add `kg/movies/movies_data.ttl` and other files for broader coverage.

5) Configure the backend to point to your dataset’s query endpoint.
- Typical Fuseki query endpoints look like `http://localhost:3030/movies/query` or `http://localhost:3030/movies/sparql`.
- Update the endpoint in `api/sparql_client.py` to match your dataset’s query URL.

### Alternative: Docker (if available)
```powershell
cd docker
docker-compose up -d
# Fuseki at http://localhost:3030/
cd ..
```
Then create/import the dataset as above.

## 4) Run the FastAPI backend
```powershell
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
- Health: `http://localhost:8000/health`
- Chat: `POST http://localhost:8000/chat` with body `{ "text": "I’m feeling happy" }`

Quick test:
```powershell
Invoke-WebRequest -Uri http://localhost:8000/health
```

Optional: set TMDb API key for external movie details (kept server-side)
```powershell
# PowerShell (session-only)
$env:TMDB_API_KEY = 'your_tmdb_api_key_here'
```
New endpoint (used by the UI for the highlight panel):
- Movie details: `POST http://localhost:8000/movie/details` with body `{ "title": "Inception", "year": "2010" }`

## 5) Run the UI (React)
```powershell
cd ui
npm install
npm start
# Open http://localhost:3000/
```
The UI calls the backend at `http://localhost:8000/`.

## Packaging (exclude `.venv` and `node_modules`)
Use one of the following methods to zip the project without heavy dependency folders.

- PowerShell unique-path approach (avoids duplicate `.gitkeep` error):
```powershell
$paths = Get-ChildItem -Recurse -File | Where-Object { $_.FullName -notmatch '\\node_modules\\' -and $_.FullName -notmatch '\\.venv\\' } | Select-Object -ExpandProperty FullName | Sort-Object -Unique
Compress-Archive -LiteralPath $paths -DestinationPath .\project.zip -Force
```

- Staging folder with Robocopy (robust directory exclusion):
```powershell
mkdir .\zip_staging
robocopy . .\zip_staging /E /XD node_modules .venv .git .ipynb_checkpoints
Compress-Archive -Path .\zip_staging -DestinationPath .\project.zip -Force
Remove-Item .\zip_staging -Recurse -Force
```

- Tar (built-in on Windows, supports excludes):
```powershell
# -a auto-selects zip format from extension
# Excludes skip all matching folders anywhere in the tree
tar.exe -a -cf project.zip --exclude=node_modules --exclude=.venv --exclude=.git --exclude='**/.ipynb_checkpoints' .
```

Tips:
- Ensure the venv folder is named `.venv` (as above) so the exclusion rules match.
- If your venv name differs (e.g., `venv`), replace `.venv` with your folder name in the commands.

## Setup on a new device (recreate `.venv` and `node_modules`)
When you receive this zip, `.venv` and `node_modules` are intentionally excluded to keep the archive small. After extracting, recreate them:

- Python environment:
```powershell
# From project root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
If you prefer not to use venv:
```powershell
python -m pip install --user -r requirements.txt
```

- UI dependencies:
```powershell
cd ui
npm install
npm start
```

- SPARQL endpoint:
Follow the "Start the SPARQL endpoint" section above to run Fuseki and load the KG, then ensure `api/sparql_client.py` points to your dataset query URL.

## Data
`data/movie_kb_final.csv` is used as a fallback when SPARQL returns no results.

## Troubleshooting
- No movies returned:
  - Confirm Fuseki is running at `http://localhost:3030/` and your dataset contains the KG files.
  - Ensure `api/sparql_client.py` points to the correct query endpoint (e.g., `http://localhost:3030/movies/query`).
- CORS issues:
  - Backend allows `allow_origins=["*"]`; confirm the API is reachable at `http://localhost:8000/`.
- Version mismatch:
  - Use Node 18+ and Python 3.10+.

## Project Structure (brief)
- `api/` FastAPI app (`main.py`)
- `nlp/` emotion mapping and follow-up logic
- `kg/` ontology and movie triples
- `ui/` React frontend
- `data/` CSV fallback
- `docker/` Fuseki docker configuration

## License
Academic/educational use. Adjust as needed for your environment.
