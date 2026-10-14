import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_data
from src.recommender import RecommendationSystem
from src.evaluator import evaluate_svd, evaluate_popularity


st.set_page_config(
    page_title="Personalized Recommender System",
    page_icon="🎬",
    layout="wide",
)

st.markdown("""
<style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        color: #777;
        margin-bottom: 1.5rem;
    }
    .movie-card {
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-bottom: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def get_data():
    return load_data()


@st.cache_resource
def get_system(movies, ratings):
    return RecommendationSystem(movies, ratings)


movies, ratings = get_data()
system = get_system(movies, ratings)

st.markdown('<div class="main-title">🎬 Personalized Recommender System</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Content-based + Collaborative Filtering + SVD Matrix Factorization</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Recommendation Settings")

    user_ids = sorted(ratings["userId"].unique().tolist())
    user_id = st.selectbox("Select user", user_ids)

    method = st.selectbox(
        "Recommendation method",
        ["Hybrid", "Content-Based", "Collaborative", "SVD"],
    )

    top_n = st.slider("Number of recommendations", 3, 12, 6)

    st.divider()
    st.caption("Try a user with only a few ratings to observe the cold-start fallback.")

history = system.user_ratings(user_id)
recommendations = system.recommend(user_id, method=method, top_n=top_n)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Users", ratings["userId"].nunique())
col2.metric("Movies", movies["movieId"].nunique())
col3.metric("Ratings", len(ratings))
col4.metric("Selected user ratings", len(history))

st.subheader("Your Personalized Recommendations")

if recommendations.empty:
    st.info("No recommendations are available for this selection.")
else:
    for _, row in recommendations.iterrows():
        with st.container(border=True):
            left, right = st.columns([4, 1])
            with left:
                st.markdown(f"### {row['title']}")
                st.write(f"**Genres:** {row.get('genres', 'N/A')}")
                if "method" in row:
                    st.caption(f"Recommendation source: {row['method']}")
            with right:
                st.metric("Score", f"{float(row['score']):.2f}")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(
    ["Rating History", "Model Evaluation", "Cold Start", "About"]
)

with tab1:
    st.subheader("User Rating History")
    if history.empty:
        st.info("This user has no rating history.")
    else:
        display = history[["title", "genres", "rating"]].copy()
        display.columns = ["Movie", "Genres", "Rating"]
        st.dataframe(display, use_container_width=True, hide_index=True)

        chart_data = (
            history.groupby("rating")
            .size()
            .rename("Number of ratings")
        )
        st.bar_chart(chart_data)

with tab2:
    st.subheader("RMSE / MAE Evaluation")
    st.write(
        "The evaluation holds out part of the rating data and measures "
        "rating-prediction error."
    )

    with st.spinner("Calculating evaluation metrics..."):
        baseline = evaluate_popularity(ratings, movies)
        svd_metrics = evaluate_svd(ratings, movies)

    evaluation = pd.DataFrame([
        {"Model": "Global Mean Baseline", **baseline},
        {"Model": "SVD Matrix Factorization", **svd_metrics},
    ])

    a, b = st.columns(2)
    a.metric("SVD RMSE", f"{svd_metrics['RMSE']:.3f}")
    b.metric("SVD MAE", f"{svd_metrics['MAE']:.3f}")

    st.dataframe(evaluation, use_container_width=True, hide_index=True)
    st.caption("Lower RMSE and MAE represent lower prediction error.")

with tab3:
    st.subheader("Cold-Start Demonstration")

    st.write(
        "Cold start occurs when the system has insufficient interaction history "
        "for a user or item."
    )

    st.markdown("""
    **Implemented strategies**
    - New user → popularity-based starter recommendations
    - Very limited user history → content + popularity fallback
    - New item → content metadata can be used without ratings
    - Normal user → personalized hybrid/model-based recommendations
    """)

    st.write("### Popularity Fallback")
    cold = system.popularity_recommendations(8)
    st.dataframe(
        cold[["title", "genres", "avg_rating", "rating_count"]]
        .rename(columns={
            "title": "Movie",
            "genres": "Genres",
            "avg_rating": "Average Rating",
            "rating_count": "Rating Count",
        }),
        use_container_width=True,
        hide_index=True,
    )

with tab4:
    st.subheader("Project Information")
    st.write("""
    This educational recommender system demonstrates the major components of
    a recommendation engine.

    **Content-based filtering:** TF-IDF and cosine similarity.

    **Collaborative filtering:** item-based similarity from the user-item
    rating matrix.

    **SVD:** latent-factor matrix factorization for predicting ratings.

    **Hybrid model:** combines content, collaborative and SVD scores.

    **Cold-start handling:** popularity and metadata-based fallback methods.

    **Evaluation:** RMSE and MAE on a held-out test split.

    **UI:** Streamlit personalized recommendation dashboard.
    """)
