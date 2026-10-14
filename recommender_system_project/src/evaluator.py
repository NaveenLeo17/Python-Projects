import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split


def split_ratings(ratings, test_size=0.2, random_state=42):
    if len(ratings) < 5:
        raise ValueError("At least 5 ratings are required for evaluation.")
    train, test = train_test_split(
        ratings,
        test_size=test_size,
        random_state=random_state,
    )
    return train.reset_index(drop=True), test.reset_index(drop=True)


def calculate_metrics(actual, predicted):
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    return {
        "RMSE": float(np.sqrt(mean_squared_error(actual, predicted))),
        "MAE": float(mean_absolute_error(actual, predicted)),
    }


def evaluate_svd(ratings, movies, n_components=8, test_size=0.2):
    from .matrix_factorization import SVDRecommender

    train, test = split_ratings(ratings, test_size=test_size)
    model = SVDRecommender(train, movies, n_components=n_components)

    actual = []
    predicted = []

    for _, row in test.iterrows():
        value = model.predict(int(row["userId"]), int(row["movieId"]))
        if np.isfinite(value):
            actual.append(float(row["rating"]))
            predicted.append(float(np.clip(value, 0.5, 5.0)))

    if not actual:
        return {"RMSE": float("nan"), "MAE": float("nan")}

    return calculate_metrics(actual, predicted)


def evaluate_popularity(ratings, movies, test_size=0.2):
    """Baseline model: predict the global mean rating."""
    _, test = split_ratings(ratings, test_size=test_size)
    mean_rating = float(ratings["rating"].mean())
    predicted = [mean_rating] * len(test)
    return calculate_metrics(test["rating"].values, predicted)
