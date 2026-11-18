
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.data_loader import load_exercises
from src.exercise_filter import filter_exercises, MUSCLE_MAP


# ---------------------------------
# CONFIGURATION
# ---------------------------------

MUSCLE_WEIGHT = 0.75
TEXT_WEIGHT = 0.25


# ---------------------------------
# HELPER FUNCTIONS
# ---------------------------------

def safe_list(value):
    """Return a list for missing muscle values."""
    return value if isinstance(value, list) else []


def get_target_muscles(selected_muscles):
    """Convert UI muscle selections into RepDB IDs."""

    targets = {}

    for group in selected_muscles:
        targets[group] = set(
            MUSCLE_MAP.get(group, [group])
        )

    return targets


# ---------------------------------
# RULE-BASED SCORING
# ---------------------------------

def calculate_muscle_score(exercise, selected_muscles):
    """
    Calculate how closely an exercise matches
    the requested muscle groups.

    Primary muscle match: 1.0
    Secondary muscle match: 0.35
    No muscle match: 0.0
    """

    targets = get_target_muscles(selected_muscles)

    if not targets:
        return 0.0

    primary = set(
        safe_list(exercise["primary_muscles"])
    )

    secondary = set(
        safe_list(exercise["secondary_muscles"])
    )

    total_score = 0.0

    for muscle_ids in targets.values():

        if primary.intersection(muscle_ids):
            total_score += 1.0

        elif secondary.intersection(muscle_ids):
            total_score += 0.35

    # Normalize to a value between 0 and 1.
    return total_score / len(targets)


# ---------------------------------
# BUILD SEARCH QUERY
# ---------------------------------

def build_query(selected_muscles):
    """
    Convert selected muscle groups into a
    text query for TF-IDF retrieval.
    """

    targets = get_target_muscles(selected_muscles)

    terms = []

    for group, muscle_ids in targets.items():
        terms.append(group)

        for muscle_id in sorted(muscle_ids):
            terms.append(
                muscle_id.replace("_", " ")
            )

    return " ".join(terms)


# ---------------------------------
# RANK EXERCISES
# ---------------------------------

def rank_exercises(
    all_exercises,
    filtered_exercises,
    selected_muscles,
    method="Hybrid",
):
    """
    Rank compatible exercises using:

    Rule-Based: muscle relevance
    TF-IDF: text cosine similarity
    Hybrid: weighted combination

    Returns a DataFrame ordered by relevance.
    """

    ranked = filtered_exercises.copy()

    if ranked.empty:
        ranked["muscle_score"] = []
        ranked["tfidf_score"] = []
        ranked["relevance_score"] = []
        return ranked

    # 1. Calculate rule-based muscle scores.
    ranked["muscle_score"] = ranked.apply(
        lambda row: calculate_muscle_score(
            row,
            selected_muscles,
        ),
        axis=1,
    )

    # 2. Fit TF-IDF on the full exercise corpus.
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True,
    )

    corpus = all_exercises["search_text"].fillna("")

    vectorizer.fit(corpus)

    # 3. Transform the compatible exercises.
    exercise_vectors = vectorizer.transform(
        ranked["search_text"].fillna("")
    )

    # 4. Transform the user query.
    query = build_query(selected_muscles)

    query_vector = vectorizer.transform([query])

    # 5. Calculate cosine similarity.
    similarities = cosine_similarity(
        query_vector,
        exercise_vectors,
    ).flatten()

    ranked["tfidf_score"] = similarities

    # 6. Select ranking approach.
    if method == "Rule-Based":

        ranked["relevance_score"] = (
            ranked["muscle_score"]
        )

    elif method == "TF-IDF":

        ranked["relevance_score"] = (
            ranked["tfidf_score"]
        )

    elif method == "Hybrid":

        ranked["relevance_score"] = (
            MUSCLE_WEIGHT * ranked["muscle_score"]
            + TEXT_WEIGHT * ranked["tfidf_score"]
        )

    else:
        raise ValueError(
            f"Unknown ranking method: {method}"
        )

    # 7. Sort by relevance, with stable tie-breaking.
    ranked = ranked.sort_values(
        by=["relevance_score", "name"],
        ascending=[False, True],
        kind="stable",
    )

    return ranked.reset_index(drop=True)


# ---------------------------------
# TEST RECOMMENDATION RANKING
# ---------------------------------

if __name__ == "__main__":

    print("\nLoading GymGenie dataset...")

    exercises = load_exercises()

    selected_equipment = [
        "Dumbbells",
        "Bench",
    ]

    selected_muscles = [
        "Chest",
        "Triceps",
    ]

    experience_level = "Beginner"

    filtered = filter_exercises(
        exercises,
        selected_equipment,
        selected_muscles,
        experience_level,
    )

    # Only strength exercises for this test.
    filtered = filtered[
        filtered["category"] == "strength"
    ].copy()

    print(f"\nCompatible exercises: {len(filtered)}")

    for method in ["Rule-Based", "TF-IDF", "Hybrid"]:

        ranked = rank_exercises(
            exercises,
            filtered,
            selected_muscles,
            method=method,
        )

        print(f"\n--- {method} TOP 5 ---")

        print(
            ranked[
                [
                    "name",
                    "muscle_score",
                    "tfidf_score",
                    "relevance_score",
                ]
            ].head(5).to_string(
                index=False,
                float_format=lambda value: f"{value:.3f}",
            )
        )
