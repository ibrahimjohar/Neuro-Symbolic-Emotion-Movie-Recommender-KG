from api.sparql_client import run_select
import os

EXTRACTION_QUERY = """
PREFIX emo: <http://www.semanticweb.org/ibrah/ontologies/2025/11/emotion-ontology#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?emotion ?genreClass WHERE {
  ?text a emo:TextualInput ;
        emo:expressesEmotion ?emotion ;
        emo:suggestsGenre ?genreInd .

  ?genreInd rdf:type ?genreClass .
}
"""

def short_prefixed(uri: str) -> str:
    # convert full URI to "emo:local"
    if "#" in uri:
        return "emo:" + uri.split("#")[-1]
    if "/" in uri:
        return "emo:" + uri.split("/")[-1]
    return uri

def build_map():
    res = run_select(EXTRACTION_QUERY)
    rows = res.get("results", {}).get("bindings", [])
    mapping = {}
    for r in rows:
        emotion = r["emotion"]["value"]
        genre_class = r["genreClass"]["value"]

        e_key = short_prefixed(emotion)
        g_key = short_prefixed(genre_class)

        mapping.setdefault(e_key, set()).add(g_key)

    # convert sets -> lists and sort for determinism
    mapping = {k: sorted(list(v)) for k, v in mapping.items()}
    return mapping

def write_file(mapping, out_path="nlp/emotion_genre_map.py"):
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Auto-generated. Maps emotion individual -> genre class (prefixed)\n")
        f.write("EMOTION_TO_GENRES = {\n")
        for k, vs in mapping.items():
            f.write(f'    "{k}": {vs!r},\n')
        f.write("}\n")

if __name__ == "__main__":
    m = build_map()
    write_file(m)
    print("Wrote nlp/emotion_genre_map.py with", len(m), "entries")
