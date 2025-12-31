import pandas as pd
import re

df = pd.read_csv("data/movies_kb_raw.csv")

#function to extract year from title
def extract_year(title):
    match = re.search(r"\((\d{4})\)", str(title))
    if match:
        return int(match.group(1))
    return None

#apply year extraction
df["year"] = df["title"].apply(extract_year)

#clean title by removing year part
df["clean_title"] = df["title"].str.replace(r"\s*\(\d{4}\)", "", regex=True)

#reorder and keep relevant cols
df_clean = df[["movieId", "clean_title", "genres", "year"]]

#rename cols to final kb schema
df_clean = df_clean.rename(columns={
    "movieId": "movie_id",
    "clean_title": "title"
})

#save intermediate cleaned kb
df_clean.to_csv("data/movies_kb_step1.csv", index=False)

print(df_clean.head())
print(f"total movies: {len(df_clean)}")
print(f"missing years: {df_clean['year'].isna().sum()}")

GENRE_MAPPING = {
    "Sci-Fi": "SciFi",
    "Film-Noir": "FilmNoir",
    "Children": "Family",
    "War": "War",
    "Drama": "Drama",
    "Comedy": "Comedy",
    "Romance": "Romance",
    "Thriller": "Thriller",
    "Horror": "Horror",
    "Action": "Action",
    "Adventure": "Adventure",
    "Fantasy": "Fantasy",
    "Animation": "Animation",
    "Documentary": "Documentary",
    "Mystery": "Mystery",
    "Crime": "Crime",
    "Musical": "Musical",
}

#normalize genres to ontology-aligned labels
def normalize_genres(genres_str):
    if pd.isna(genres_str):
        return None
    
    raw_genres = genres_str.split("|")
    mapped = []
    
    for g in raw_genres:
        if g in GENRE_MAPPING:
            mapped.append(GENRE_MAPPING[g])
            
    #removing duplicates while preserving order
    mapped = list(dict.fromkeys(mapped))
    
    if not mapped:
        return None
    
    return "|".join(mapped)


df_clean["genres_normalized"] = df_clean["genres"].apply(normalize_genres)
#drop movie with no mappable genres
df_clean = df_clean.dropna(subset=["genres_normalized"])

df_clean = df_clean[~df_clean["genres_normalized"].str.contains("Western", na=False)]

#keep final cols
df_final = df_clean[["movie_id", "title", "year", "genres_normalized"]]
#save final kb
df_final.to_csv("data/movie_kb_final.csv", index=False)

print(df_final.head())
print(f"total movies after genre normalization: {len(df_final)}")
