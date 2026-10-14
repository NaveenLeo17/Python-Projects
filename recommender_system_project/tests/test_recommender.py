import unittest
import pandas as pd

from src.content_based import ContentBasedRecommender
from src.collaborative import CollaborativeRecommender
from src.matrix_factorization import SVDRecommender
from src.recommender import RecommendationSystem
from src.evaluator import calculate_metrics


class TestRecommenderSystem(unittest.TestCase):
    def setUp(self):
        self.movies = pd.DataFrame([
            {"movieId": 1, "title": "Space Mission", "genres": "Sci-Fi|Adventure",
             "description": "A crew explores a distant planet."},
            {"movieId": 2, "title": "Galaxy War", "genres": "Sci-Fi|Action",
             "description": "Heroes fight across a galaxy."},
            {"movieId": 3, "title": "Ocean Love", "genres": "Romance|Drama",
             "description": "Two people meet beside the ocean."},
            {"movieId": 4, "title": "Robot Future", "genres": "Sci-Fi|Drama",
             "description": "A robot discovers human emotions."},
            {"movieId": 5, "title": "Mountain Quest", "genres": "Adventure|Fantasy",
             "description": "Friends begin a dangerous mountain journey."},
        ])

        self.ratings = pd.DataFrame([
            {"userId": 1, "movieId": 1, "rating": 5.0},
            {"userId": 1, "movieId": 2, "rating": 4.5},
            {"userId": 1, "movieId": 3, "rating": 2.0},
            {"userId": 2, "movieId": 1, "rating": 4.5},
            {"userId": 2, "movieId": 2, "rating": 5.0},
            {"userId": 2, "movieId": 4, "rating": 4.0},
            {"userId": 3, "movieId": 3, "rating": 5.0},
            {"userId": 3, "movieId": 5, "rating": 4.5},
            {"userId": 4, "movieId": 4, "rating": 5.0},
            {"userId": 4, "movieId": 5, "rating": 4.0},
        ])

    def test_content_recommender(self):
        model = ContentBasedRecommender(self.movies)
        result = model.similar_items(1, 2)
        self.assertGreaterEqual(len(result), 1)

    def test_collaborative_recommender(self):
        model = CollaborativeRecommender(self.ratings, self.movies)
        result = model.recommend_for_user(1, 2)
        self.assertIsNotNone(result)

    def test_svd_recommender(self):
        model = SVDRecommender(self.ratings, self.movies, n_components=2)
        prediction = model.predict(1, 4)
        self.assertTrue(prediction == prediction)  # not NaN

    def test_metrics(self):
        metrics = calculate_metrics([1, 2, 3], [1, 2, 4])
        self.assertAlmostEqual(metrics["MAE"], 1 / 3)
        self.assertAlmostEqual(metrics["RMSE"], (1 / 3) ** 0.5)

    def test_system_recommendations(self):
        system = RecommendationSystem(self.movies, self.ratings)
        result = system.recommend(1, method="Hybrid", top_n=2)
        self.assertLessEqual(len(result), 2)

    def test_new_user_fallback(self):
        system = RecommendationSystem(self.movies, self.ratings)
        result = system.recommend(999, method="Hybrid", top_n=3)
        self.assertEqual(len(result), 3)


if __name__ == "__main__":
    unittest.main()
