import requests

JENA_ENDPOINT = "http://localhost:3030/emotion/sparql"

def run_query(query: str):
    r = requests.post(
        JENA_ENDPOINT,
        data=query.encode("utf-8"),
        headers={
            "Content-Type": "application/sparql-query",
            "Accept": "application/sparql-results+json",
        },
        timeout=30
    )

    #CRITICAL: surface Jena errors instead of crashing blindly
    if not r.ok:
        raise RuntimeError(
            f"Jena error {r.status_code}:\n{r.text}"
        )

    return r.json()
