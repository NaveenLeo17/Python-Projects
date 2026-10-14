import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


class CollaborativeRecommender:
    """Simple item-based collaborative filtering recommender."""

    def __init__(self, ratings: pd.DataFrame, movies: pd.DataFrame):
        self.ratings = ratings.copy()
        self.movies = movies.copy()

        self.matrix = self.ratings.pivot_table(
            index="userId",
            columns="movieId",
            values="rating",
            fill_value=0,
        )

        self.movie_ids = list(self.matrix.columns)
        if len(self.movie_ids):
            self.similarity = cosine_similarity(self.matrix.T)
        else:
            self.similarity = np.empty((0, 0))

        self.index_by_movie = {
            movie_id: idx for idx, movie_id in enumerate(self.movie_ids)
        }

    def recommend_for_user(self, user_id, top_n=10):
        if user_id not in self.matrix.index or not self.movie_ids:
            return pd.DataFrame(columns=["movieId", "title", "score"])

        user_vector = self.matrix.loc[user_id].values.astype(float)
        rated_indices = np.where(user_vector > 0)[0]

        if len(rated_indices) == 0:
            return pd.DataFrame(columns=["movieId", "title", "score"])

        weighted_scores = np.zeros(len(self.movie_ids), dtype=float)
        similarity_weights = np.zeros(len(self.movie_ids), dtype=float)

        for idx in rated_indices:
            rating = user_vector[idx]
            similarity_row = self.similarity[idx]
            weighted_scores += similarity_row * rating
            similarity_weights += np.abs(similarity_row)

        predictions = np.divide(
            weighted_scores,
            similarity_weights,
            out=np.zeros_like(weighted_scores),
            where=similarity_weights > 0,
        )

        rows = []
        for idx, score in enumerate(predictions):
            movie_id = self.movie_ids[idx]
            if user_vector[idx] > 0:
                continue
            rows.append({
                "movieId": int(movie_id),
                "score": float(score),
            })

        result = pd.DataFrame(rows)
        if result.empty:
            return result

        result = result.sort_values("score", ascending=False).head(top_n)
        result = result.merge(
            self.movies[["movieId", "title", "genres"]],
            on="movieId",
            how="left",
        )
        return result[["movieId", "title", "genres", "score"]].reset_index(drop=True)
