import requests

JENA_SELECT_ENDPOINT = "http://localhost:3030/emotion/sparql"
JENA_UPDATE_ENDPOINT = "http://localhost:3030/emotion/update"

def run_select(query: str, timeout: int = 30) -> dict:
    r = requests.post(
        JENA_SELECT_ENDPOINT,
        data={"query": query},
        headers={"Accept": "application/sparql-results+json"}
    )
    r.raise_for_status()
    return r.json()

def run_update(update_query: str, timeout: int = 30) -> None:
    r = requests.post(
        JENA_UPDATE_ENDPOINT,
        data=update_query.encode("utf-8"),
        headers={"Content-Type": "application/sparql-update"}
    )
    r.raise_for_status()