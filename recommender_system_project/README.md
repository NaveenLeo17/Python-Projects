# Personalized Recommender System

A complete Python project demonstrating:

- Content-based filtering
- Collaborative filtering
- Matrix factorization using SVD
- Evaluation using RMSE and MAE
- Cold-start problem handling
- Streamlit user interface
- Personalized recommendation dashboard
- Hybrid recommendations combining multiple approaches
- Sample movie-rating dataset
- Basic unit tests

## 1. Project Structure

```text
recommender_system_project/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   ├── movies.csv
│   └── ratings.csv
├── src/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── content_based.py
│   ├── collaborative.py
│   ├── matrix_factorization.py
│   ├── evaluator.py
│   └── recommender.py
└── tests/
    └── test_recommender.py
```

## 2. Features

### Content-Based Filtering
Uses movie genres and descriptions to calculate TF-IDF vectors and cosine similarity. Recommendations are based on items similar to movies the user has liked.

### Collaborative Filtering
Uses user-item ratings and item-item/user-item similarity. Recommendations are generated from the behavior of similar users.

### Matrix Factorization / SVD
The project uses Truncated SVD to learn latent factors from the user-item rating matrix. These latent factors are used to estimate missing ratings and generate recommendations.

### Evaluation
The application evaluates rating prediction using:

- RMSE — Root Mean Squared Error
- MAE — Mean Absolute Error

The evaluation uses a held-out test set from the ratings data.

### Cold-Start Handling
The project handles:

- New users: recommends popular, high-rated items using a popularity score.
- Users with only a few ratings: combines popularity with content-based recommendations.
- New items: uses content metadata such as genres and descriptions.
- Completely new users: provides a starter recommendation list.

### Personalized Dashboard
The Streamlit dashboard allows a user to:

1. Select a user profile.
2. Select recommendation method.
3. Set the number of recommendations.
4. View personalized recommendations.
5. See predicted scores.
6. View user rating history.
7. Inspect model evaluation metrics.
8. Explore cold-start recommendations.

## 3. Installation

Use Python 3.10 or newer.

Create and activate a virtual environment:

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 4. Run the Dashboard

From the project root:

```bash
streamlit run app.py
```

The browser should open automatically. If not, open the URL shown in the terminal.

## 5. Run Tests

```bash
python -m unittest discover tests
```

## 6. How the System Works

The system has three recommendation engines.

### A. Content-Based

1. Combine movie title, genres and description.
2. Convert text to TF-IDF vectors.
3. Calculate cosine similarity.
4. Find movies similar to the user's highly rated movies.
5. Remove movies already rated by the user.
6. Return the highest-scoring unseen movies.

### B. Collaborative Filtering

1. Construct a user-item rating matrix.
2. Calculate item similarity using rating vectors.
3. Identify movies related to movies the user rated highly.
4. Estimate scores for unseen movies.
5. Rank candidates.

### C. SVD Matrix Factorization

The rating matrix is decomposed approximately as:

```text
R ≈ U × Σ × Vᵀ
```

where:

- `R` = user-item rating matrix
- `U` = user latent factors
- `Σ` = singular values
- `Vᵀ` = item latent factors

The reconstructed matrix provides predicted ratings.

## 7. Evaluation

The evaluator hides a portion of known ratings and compares actual ratings against predictions.

```text
RMSE = sqrt(mean((actual - predicted)^2))

MAE = mean(abs(actual - predicted))
```

Lower values indicate smaller prediction errors.

Because this project includes a small educational sample dataset, the metrics are intended for demonstrating the evaluation process rather than benchmarking a production recommender.

## 8. Cold Start

Cold start is a common recommender-system problem where there is insufficient historical interaction data.

This implementation uses a fallback hierarchy:

```text
Enough user history
       ↓
Hybrid recommendation
       ↓
Limited user history
       ↓
Content + popularity
       ↓
New user
       ↓
Popularity-based starter recommendations
```

For a brand-new item, metadata-based content recommendations can still work without ratings.

## 9. Customizing the Dataset

Replace:

```text
data/movies.csv
data/ratings.csv
```

with your own data while preserving the required columns.

### movies.csv

Required:

```text
movieId,title,genres,description
```

### ratings.csv

Required:

```text
userId,movieId,rating,timestamp
```

## 10. Educational Requirements Covered

| Requirement | Implementation |
|---|---|
| Content-based filtering | TF-IDF + cosine similarity |
| Collaborative filtering | Item-based rating similarity |
| Matrix factorization | Truncated SVD |
| RMSE | `src/evaluator.py` |
| MAE | `src/evaluator.py` |
| Cold-start problem | Popularity/content fallback |
| User interface | Streamlit |
| Personalized dashboard | `app.py` |
| Data handling | Pandas |
| Visualization | Streamlit charts/metrics |
| Testing | `tests/test_recommender.py` |

## 11. Possible Future Improvements

- Add real MovieLens data.
- Add login/authentication.
- Store user interactions in a database.
- Add implicit feedback such as clicks and watch time.
- Add neural collaborative filtering.
- Add model persistence.
- Add scheduled model retraining.
- Deploy using Streamlit Community Cloud, Docker, or another hosting service.
