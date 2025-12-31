import pandas as pd
from pathlib import Path

BASE_URI = "http://www.semanticweb.org/ibrah/ontologies/2025/11/emotion-ontology#"
OUTPUT_TTL = Path("kg/movies.ttl")

#load FULL dataset
df = pd.read_csv("data/movie_kb_final.csv")

ttl_lines = []
ttl_lines.append(f"@prefix emo: <{BASE_URI}> .")
ttl_lines.append("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n")

for _, row in df.iterrows():
    movie_uri = f"emo:movie_{int(row.movie_id)}"
    title = str(row.title).replace('"', "'")

    ttl_lines.append(f"{movie_uri} a emo:Movie ;")
    ttl_lines.append(f'  emo:title "{title}" ;')

    if not pd.isna(row.year):
        ttl_lines.append(f'  emo:year "{int(row.year)}"^^xsd:gYear ;')

    #genres → GENRE CLASSES (already normalized)
    genres = row.genres_normalized.split("|")
    for g in genres:
        ttl_lines.append(f"  emo:belongsToGenre emo:{g} ;")

    #fix last semicolon
    ttl_lines[-1] = ttl_lines[-1].rstrip(" ;") + " .\n"

OUTPUT_TTL.write_text("\n".join(ttl_lines), encoding="utf-8")

print(f"SUCCESS: Exported {len(df)} movies to {OUTPUT_TTL}")