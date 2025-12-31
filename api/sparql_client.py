import requests

JENA_ENDPOINT = "http://localhost:3030/emotion/sparql"

def run_query(query: str):
    r = requests.post(
        JENA_ENDPOINT,
        data={"query": query},
        headers={"Accept": "application/sparql+json"}
    )
    r.raise_for_status()
    return r.json()