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