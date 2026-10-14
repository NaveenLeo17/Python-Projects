import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class ContentBasedRecommender:
    def __init__(self, movies: pd.DataFrame):
        self.movies = movies.reset_index(drop=True).copy()
        self.movies["content"] = (
            self.movies["genres"].fillna("").str.replace("|", " ", regex=False)
            + " "
            + self.movies["description"].fillna("")
        )
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(self.movies["content"])
        self.similarity = cosine_similarity(self.matrix)

        self.index_by_movie = {
            int(movie_id): idx
            for idx, movie_id in enumerate(self.movies["movieId"])
        }

    def similar_items(self, movie_id, top_n=10):
        movie_id = int(movie_id)
        if movie_id not in self.index_by_movie:
            return pd.DataFrame(columns=["movieId", "title", "score"])

        idx = self.index_by_movie[movie_id]
        scores = self.similarity[idx]
        order = np.argsort(scores)[::-1]

        rows = []
        for i in order:
            if i == idx:
                continue
            rows.append({
                "movieId": int(self.movies.iloc[i]["movieId"]),
                "title": self.movies.iloc[i]["title"],
                "score": float(scores[i]),
            })
            if len(rows) >= top_n:
                break

        return pd.DataFrame(rows)

    def recommend_for_user(self, user_ratings, top_n=10, min_rating=4.0):
        if user_ratings is None or user_ratings.empty:
            return pd.DataFrame(columns=["movieId", "title", "score"])

        seen = set(user_ratings["movieId"].astype(int))
        liked = user_ratings[user_ratings["rating"] >= min_rating]

        if liked.empty:
            liked = user_ratings.sort_values("rating", ascending=False).head(3)

        scores = np.zeros(len(self.movies), dtype=float)
        weights = np.zeros(len(self.movies), dtype=float)

        for _, row in liked.iterrows():
            movie_id = int(row["movieId"])
            idx = self.index_by_movie.get(movie_id)
            if idx is None:
                continue
            weight = max(float(row["rating"]) - 2.5, 0.5)
            scores += self.similarity[idx] * weight
            weights += weight

        normalized = np.divide(
            scores,
            weights,
            out=np.zeros_like(scores),
            where=weights > 0,
        )

        candidates = []
        for idx, value in enumerate(normalized):
            movie_id = int(self.movies.iloc[idx]["movieId"])
            if movie_id in seen:
                continue
            candidates.append({
                "movieId": movie_id,
                "title": self.movies.iloc[idx]["title"],
                "score": float(value),
            })

        result = pd.DataFrame(candidates)
        if result.empty:
            return result
        return result.sort_values("score", ascending=False).head(top_n).reset_index(drop=True)
