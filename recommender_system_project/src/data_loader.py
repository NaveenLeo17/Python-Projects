from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def load_movies(path=None):
    path = path or DATA_DIR / "movies.csv"
    movies = pd.read_csv(path)
    required = {"movieId", "title", "genres", "description"}
    missing = required - set(movies.columns)
    if missing:
        raise ValueError(f"movies.csv is missing columns: {sorted(missing)}")
    movies["movieId"] = movies["movieId"].astype(int)
    movies["genres"] = movies["genres"].fillna("")
    movies["description"] = movies["description"].fillna("")
    return movies


def load_ratings(path=None):
    path = path or DATA_DIR / "ratings.csv"
    ratings = pd.read_csv(path)
    required = {"userId", "movieId", "rating"}
    missing = required - set(ratings.columns)
    if missing:
        raise ValueError(f"ratings.csv is missing columns: {sorted(missing)}")
    ratings["userId"] = ratings["userId"].astype(int)
    ratings["movieId"] = ratings["movieId"].astype(int)
    ratings["rating"] = ratings["rating"].astype(float)
    return ratings


def load_data():
    return load_movies(), load_ratings()
