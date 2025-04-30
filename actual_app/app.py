from flask import Flask, render_template, request
import pandas as pd
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
import os

app = Flask(__name__)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(APP_ROOT, "cleaned_I_THINK.csv")

try:
    data = pd.read_csv(CSV_PATH)
    print(f"Successfully loaded data from {CSV_PATH}")

    if "genres" in data.columns:
        try:
            data["genres"] = data["genres"].apply(
                lambda x: eval(x) if isinstance(x, str) else x
            )
        except Exception as e:
            print(
                f"Warning: Could not evaluate 'genres' column. Error: {e}. Treating genres as empty lists."
            )
            data["genres"] = data["genres"].apply(
                lambda x: [] if isinstance(x, str) else x
            )

        data["genres"] = data["genres"].apply(
            lambda x: x if isinstance(x, list) else []
        )
        data["genres_string"] = data["genres"].apply(
            lambda x: ", ".join(sorted(map(str, x)))
        )
    else:
        print(
            "Warning: 'genres' column not found in CSV. Genre-based features will be unavailable."
        )
        data["genres"] = pd.Series([[] for _ in range(len(data))])
        data["genres_string"] = ""

    if "user_rating" in data.columns:
        data["user_rating"] = pd.to_numeric(
            data["user_rating"], errors="coerce"
        ).fillna(0.0)
    else:
        print(
            "Warning: 'user_rating' column not found. Defaulting ratings to 0.0."
        )
        data["user_rating"] = 0.0

    if "release_year" not in data.columns:
        print(
            "Warning: 'release_year' column not found. Collaborative filtering and release year filtering might fail."
        )
        data["release_year"] = 0

    if "title" not in data.columns:
        raise ValueError(
            "'title' column is essential and not found in the CSV."
        )

except FileNotFoundError:
    print(f"FATAL ERROR: Could not find the data file at {CSV_PATH}")
    raise SystemExit(f"Error: Data file not found at {CSV_PATH}")
except Exception as e:
    print(
        f"FATAL ERROR: An error occurred during data loading or initial preprocessing: {e}"
    )
    raise SystemExit(f"Error during data loading: {e}")


genres_list = [
    "Action",
    "Adventure",
    "Animation",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Family",
    "Fantasy",
    "History",
    "Horror",
    "Music",
    "Mystery",
    "Romance",
    "Science Fiction",
    "TV Movie",
    "Thriller",
    "War",
    "Western",
]


def recommend_content_based(input_genres, top_n=10):
    """Recommends movies based on genre similarity (Jaccard Index)."""
    if "genres" not in data.columns or data["genres"].isnull().all():
        print(
            "Content-based filtering skipped: 'genres' column missing or empty."
        )
        return []

    input_genres_set = set(input_genres)
    if not input_genres_set:
        return []

    def genre_similarity(movie_genres):
        movie_genres_set = (
            set(movie_genres) if isinstance(movie_genres, list) else set()
        )
        union_size = len(input_genres_set.union(movie_genres_set))
        if union_size == 0:
            return 0.0
        return (
            len(input_genres_set.intersection(movie_genres_set)) / union_size
        )

    data["similarity"] = data["genres"].apply(genre_similarity)
    recommendations = data.sort_values(by="similarity", ascending=False).head(
        top_n
    )
    return recommendations[["title", "genres_string", "user_rating"]].to_dict(
        "records"
    )


def collaborative_filtering(top_n=10):
    """Recommends movies using SVD and K-Nearest Neighbors on a user-item matrix."""
    if (
        "title" not in data.columns
        or "release_year" not in data.columns
        or "user_rating" not in data.columns
    ):
        print(
            "Collaborative filtering skipped: Missing required columns (title, release_year, user_rating)."
        )
        return [], "N/A"

    try:

        user_item_matrix = pd.pivot_table(
            data,
            values="user_rating",
            index="title",
            columns="release_year",
            fill_value=0,
        )

        if user_item_matrix.empty:
            print(
                "Collaborative filtering skipped: User-item matrix is empty."
            )
            return [], "N/A"

        scaler = StandardScaler()
        user_item_matrix_scaled = scaler.fit_transform(user_item_matrix)

        n_components = min(20, user_item_matrix_scaled.shape[1] - 1)
        if n_components <= 0:
            print(
                "Collaborative filtering skipped: Not enough features for SVD."
            )
            return [], "N/A"

        svd = TruncatedSVD(n_components=n_components, random_state=42)
        matrix_svd = svd.fit_transform(user_item_matrix_scaled)

        model_knn = NearestNeighbors(metric="cosine", algorithm="brute")
        model_knn.fit(matrix_svd)

        if not user_item_matrix.index.empty:
            random_movie_title = np.random.choice(
                user_item_matrix.index, size=1
            )[0]
            try:
                movie_idx = user_item_matrix.index.get_loc(random_movie_title)
                distances, indices = model_knn.kneighbors(
                    [matrix_svd[movie_idx]], n_neighbors=top_n + 1
                )

                recommendations = [
                    {"title": user_item_matrix.index[i]}
                    for i in indices.flatten()[1:]
                ]
                return recommendations, random_movie_title
            except KeyError:
                print(
                    f"Collaborative filtering error: Randomly selected movie '{random_movie_title}' not found in matrix index."
                )
                return [], "N/A"
        else:
            print(
                "Collaborative filtering skipped: No movies available in the user-item matrix index."
            )
            return [], "N/A"

    except Exception as e:
        print(f"Error during collaborative filtering: {e}")
        return [], "N/A"


def filter_movies(
    search_title,
    selected_genres,
    all_genres,
    sort_rating,
    only_released,
    top_n=20,
):
    """Filters the movie dataset based on various criteria."""
    filtered = data.copy()

    if search_title:
        search_title_str = str(search_title)
        title_mask = filtered["title"].str.contains(
            search_title_str, case=False, na=False
        )
        filtered_by_title = filtered[title_mask]

        if not filtered_by_title.empty and "genres" in filtered.columns:
            base_movie_genres = set(filtered_by_title.iloc[0]["genres"])
            if base_movie_genres:

                def has_similar_genres(movie_genres):
                    return len(set(movie_genres) & base_movie_genres) >= 3

                similar_movies = data[data["genres"].apply(has_similar_genres)]

                filtered = (
                    pd.concat([filtered_by_title, similar_movies])
                    .drop_duplicates(subset=["title", "release_year"])
                    .reset_index(drop=True)
                )
            else:

                filtered = filtered_by_title
        else:

            filtered = filtered_by_title

    if selected_genres and "genres" in filtered.columns:
        selected_genres_set = set(selected_genres)
        if all_genres:
            genre_mask = filtered["genres"].apply(
                lambda x: selected_genres_set.issubset(set(x))
            )
        else:
            genre_mask = filtered["genres"].apply(
                lambda x: bool(set(x) & selected_genres_set)
            )
        filtered = filtered[genre_mask]

    if only_released and "release_year" in filtered.columns:
        try:
            current_year = pd.Timestamp.now().year

            release_year_numeric = pd.to_numeric(
                filtered["release_year"], errors="coerce"
            )
            filtered = filtered[release_year_numeric <= current_year]
        except Exception as e:
            print(f"Warning: Could not filter by release year. Error: {e}")

    if sort_rating and "user_rating" in filtered.columns:
        filtered = filtered.sort_values(by="user_rating", ascending=False)

    return filtered.head(top_n).to_dict("records")


@app.route("/")
def home():
    """Renders the home page with the genre list for filtering."""
    return render_template("index.html", genres_list=genres_list)


@app.route("/filter", methods=["POST"])
def filter_route():
    """Handles the form submission for filtering movies."""
    try:
        search_title = request.form.get("search_title", "")
        selected_genres = request.form.getlist("selected_genres")

        all_genres = request.form.get("all_genres") == "on"
        sort_rating = request.form.get("sort_rating") == "on"
        only_released = request.form.get("only_released") == "on"

        print(
            f"Filtering with: title='{search_title}', genres={selected_genres}, all_genres={all_genres}, sort_rating={sort_rating}, only_released={only_released}"
        )

        recommendations = filter_movies(
            search_title,
            selected_genres,
            all_genres,
            sort_rating,
            only_released,
        )
        print(f"Found {len(recommendations)} filtered recommendations.")

        return render_template(
            "recommendations.html",
            recommendations=recommendations,
            filter_criteria=request.form.to_dict(),
        )
    except Exception as e:
        print(f"Error in /filter route: {e}")

        return render_template(
            "index.html",
            genres_list=genres_list,
            error="An error occurred during filtering.",
        )


@app.route("/content_based", methods=["POST"])
def content_based_route():
    """Handles the form submission for content-based recommendations."""
    try:
        selected_genres = request.form.getlist("selected_genres")
        if not selected_genres:
            return render_template(
                "recommendations.html",
                recommendations=[],
                message="Please select at least one genre for content-based recommendations.",
            )

        print(f"Content-based filtering for genres: {selected_genres}")
        recommendations = recommend_content_based(selected_genres, top_n=10)
        print(f"Found {len(recommendations)} content-based recommendations.")

        return render_template(
            "recommendations.html",
            recommendations=recommendations,
            method="Content-Based (Genre Similarity)",
        )
    except Exception as e:
        print(f"Error in /content_based route: {e}")
        return render_template(
            "index.html",
            genres_list=genres_list,
            error="An error occurred during content-based recommendation.",
        )


@app.route("/collaborative", methods=["POST"])
def collaborative_route():
    """Handles the request for collaborative filtering recommendations."""
    try:
        print("Generating collaborative filtering recommendations...")
        recommendations, base_movie = collaborative_filtering(top_n=10)
        print(
            f"Found {len(recommendations)} collaborative recommendations based on '{base_movie}'."
        )

        return render_template(
            "recommendations.html",
            recommendations=recommendations,
            base_movie=base_movie,
            method="Collaborative Filtering (User-Item Similarity)",
        )
    except Exception as e:
        print(f"Error in /collaborative route: {e}")
        return render_template(
            "index.html",
            genres_list=genres_list,
            error="An error occurred during collaborative filtering recommendation.",
        )


if __name__ == "__main__":

    print("Starting Flask development server...")
    app.run(host="0.0.0.0", port=5000, debug=True)
