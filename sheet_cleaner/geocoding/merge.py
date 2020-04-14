"""Script that merges all geo_admin tabs exported to tsv into a single tsv file."""
import pandas as pd
import numpy as np

want_cols = ["input", "latitude", "longitude", "geo_resolution", "location", "admin3", "admin2", "admin1", "country_new", "admin_id"]

inputs = [
    "/Users/timothe/Downloads/LATAM _ Open COVID-19 Working Group - geo_admin.tsv",
    "/Users/timothe/Downloads/New York, USA _ Open COVID-19 Working Group - geo_admin.tsv",
    "/Users/timothe/Downloads/Asia_Oceania _ Open COVID-19 Working Group - geo_admin.tsv",
    "/Users/timothe/Downloads/Africa _ Open COVID-19 Working Group - geo_admin.tsv",    
]

all_df = pd.DataFrame()
for i in inputs:
    df = pd.read_csv(i, delimiter="\t")
    if "latitude.1" in df.columns:
        df["latitude"] = df["latitude.1"]
    if "longitude.1" in df.columns:
        df["longitude"] = df["longitude.1"]
    if "geo_resolution.1" in df.columns:
        df["geo_resolution"] = df["geo_resolution.1"]
    df = df[want_cols]
    all_df = all_df.append(df)

# Remove invalid entries (without lat, lng or input).
all_df.input = all_df.input.str.strip()
all_df.input.replace('', np.nan, inplace=True)
all_df.dropna(subset=["latitude", "longitude", "input"])

# Drop duplicate rows.
all_df.drop_duplicates(inplace=True)

# Sort by row index.
all_df.sort_index(inplace=True)

# print(all_df)
# for col in want_cols:
#     print(col, all_df[col].describe())
#     print("\n")

all_df.to_csv("/tmp/geo_admin.tsv", sep="\t", header=False, index=False)