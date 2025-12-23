import pandas as pd
from pathlib import Path

BASE_URI = "http://www.semanticweb.org/ibrah/ontologies/2025/11/emotion-ontology#"
OUTPUT_TTL = Path("kg/movies_1000.ttl")

df = pd.read_csv("data/movie_kb_final.csv").head(1000)

ttl_lines = []
ttl_lines.append(f"@prefix emo: <{BASE_URI}> .")
ttl_lines.append("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n")

for _, row in df.iterrows():
    movie_uri = f"emo:movie_{int(row.movie_id)}"
    title = row.title.replace('"', "'")
    year = int(row.year)

    ttl_lines.append(f"{movie_uri} a emo:Movie ;")
    ttl_lines.append(f'  emo:title "{title}" ;')
    ttl_lines.append(f'  emo:releaseYear "{year}"^^xsd:gYear ;')

    genres = row.genres_normalized.split("|")
    for g in genres:
        genre_uri = g.replace(" ", "").replace("-", "")
        ttl_lines.append(f"  emo:belongsToGenre emo:{genre_uri} ;")

    # fix last semicolon
    ttl_lines[-1] = ttl_lines[-1].rstrip(" ;") + " .\n"

OUTPUT_TTL.write_text("\n".join(ttl_lines), encoding="utf-8")

print(f"✅ Exported {len(df)} movies to {OUTPUT_TTL}")