import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD


class SVDRecommender:
    """Latent-factor recommender using Truncated SVD."""

    def __init__(self, ratings: pd.DataFrame, movies: pd.DataFrame, n_components=8):
        self.ratings = ratings.copy()
        self.movies = movies.copy()

        self.matrix = self.ratings.pivot_table(
            index="userId",
            columns="movieId",
            values="rating",
            fill_value=0,
        )

        self.user_ids = list(self.matrix.index)
        self.movie_ids = list(self.matrix.columns)
        self.user_index = {uid: i for i, uid in enumerate(self.user_ids)}

        if len(self.movie_ids) >= 2 and len(self.user_ids) >= 2:
            max_components = min(len(self.user_ids), len(self.movie_ids)) - 1
            components = max(1, min(n_components, max_components))
            self.model = TruncatedSVD(
                n_components=components,
                random_state=42
            )
            self.reduced = self.model.fit_transform(self.matrix.values)
            self.reconstructed = self.model.inverse_transform(self.reduced)
        else:
            self.model = None
            self.reconstructed = self.matrix.values.astype(float)

        self.predictions = pd.DataFrame(
            self.reconstructed,
            index=self.user_ids,
            columns=self.movie_ids,
        )

    def predict(self, user_id, movie_id):
        if user_id not in self.predictions.index or movie_id not in self.predictions.columns:
            return np.nan
        return float(self.predictions.loc[user_id, movie_id])

    def recommend_for_user(self, user_id, top_n=10):
        if user_id not in self.predictions.index:
            return pd.DataFrame(columns=["movieId", "title", "score"])

        seen = set(
            self.ratings.loc[self.ratings["userId"] == user_id, "movieId"].astype(int)
        )

        row = self.predictions.loc[user_id].copy()
        candidates = row[~row.index.isin(seen)].sort_values(ascending=False).head(top_n)

        result = pd.DataFrame({
            "movieId": candidates.index.astype(int),
            "score": candidates.values.astype(float),
        })

        return result.merge(
            self.movies[["movieId", "title", "genres"]],
            on="movieId",
            how="left",
        )[["movieId", "title", "genres", "score"]]
