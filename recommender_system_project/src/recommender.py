import numpy as np
import pandas as pd


class RecommendationSystem:
    def __init__(self, movies, ratings):
        from .content_based import ContentBasedRecommender
        from .collaborative import CollaborativeRecommender
        from .matrix_factorization import SVDRecommender

        self.movies = movies.copy()
        self.ratings = ratings.copy()

        self.content = ContentBasedRecommender(self.movies)
        self.collaborative = CollaborativeRecommender(self.ratings, self.movies)
        self.svd = SVDRecommender(self.ratings, self.movies)

        self.global_mean = float(self.ratings["rating"].mean())
        self.movie_stats = (
            self.ratings.groupby("movieId")
            .agg(avg_rating=("rating", "mean"), rating_count=("rating", "count"))
            .reset_index()
        )

    def popularity_recommendations(self, top_n=10):
        stats = self.movie_stats.copy()
        stats["score"] = (
            stats["avg_rating"] * 0.65
            + np.log1p(stats["rating_count"]) * 0.35
        )

        result = stats.sort_values(
            ["score", "rating_count"],
            ascending=False,
        ).head(top_n)

        return result.merge(
            self.movies[["movieId", "title", "genres"]],
            on="movieId",
            how="left",
        )[["movieId", "title", "genres", "avg_rating", "rating_count", "score"]]

    def user_ratings(self, user_id):
        return (
            self.ratings[self.ratings["userId"] == user_id]
            .merge(self.movies[["movieId", "title", "genres"]], on="movieId")
            .sort_values("rating", ascending=False)
        )

    def _cold_start(self, user_id, top_n):
        user_history = self.user_ratings(user_id)

        if user_history.empty:
            result = self.popularity_recommendations(top_n)
            result["method"] = "Popularity fallback (new user)"
            return result

        if len(user_history) < 3:
            content = self.content.recommend_for_user(user_history, top_n=top_n)
            if not content.empty:
                content["method"] = "Content + popularity (limited history)"
                return content
            result = self.popularity_recommendations(top_n)
            result["method"] = "Popularity fallback"
            return result

        return None

    def recommend(self, user_id, method="Hybrid", top_n=10):
        cold = self._cold_start(user_id, top_n)
        if cold is not None:
            return cold

        history = self.user_ratings(user_id)
        seen = set(history["movieId"].astype(int))

        if method == "Content-Based":
            result = self.content.recommend_for_user(history, top_n)
        elif method == "Collaborative":
            result = self.collaborative.recommend_for_user(user_id, top_n)
        elif method == "SVD":
            result = self.svd.recommend_for_user(user_id, top_n)
        else:
            result = self._hybrid(history, user_id, top_n)

        if result.empty:
            result = self.popularity_recommendations(top_n)
            result["method"] = "Popularity fallback"
            return result

        result = result[~result["movieId"].isin(seen)].copy()
        result["method"] = method
        return result.head(top_n).reset_index(drop=True)

    def _hybrid(self, history, user_id, top_n):
        content = self.content.recommend_for_user(history, top_n=50)
        collab = self.collaborative.recommend_for_user(user_id, top_n=50)
        svd = self.svd.recommend_for_user(user_id, top_n=50)

        candidates = {}

        for df, weight in [(content, 0.35), (collab, 0.30), (svd, 0.35)]:
            if df.empty:
                continue
            for _, row in df.iterrows():
                movie_id = int(row["movieId"])
                candidates.setdefault(movie_id, 0.0)
                candidates[movie_id] += float(row["score"]) * weight

        if not candidates:
            return pd.DataFrame()

        result = pd.DataFrame(
            [{"movieId": k, "score": v} for k, v in candidates.items()]
        ).sort_values("score", ascending=False)

        return result.merge(
            self.movies[["movieId", "title", "genres"]],
            on="movieId",
            how="left",
        )[["movieId", "title", "genres", "score"]].head(top_n)
