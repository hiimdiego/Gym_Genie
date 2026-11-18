
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.data_loader import load_exercises
from src.exercise_filter import (
    filter_by_equipment,
    filter_by_difficulty,
)
from src.workout import get_exercise_family


# ---------------------------------
# HELPER FUNCTIONS
# ---------------------------------

def safe_list(value):
    """Return a list for missing fields."""
    return value if isinstance(value, list) else []


def get_substitutions(
    original_exercise,
    all_exercises,
    available_equipment,
    experience_level,
    excluded_ids=None,
    max_results=5,
):
    """
    Find equipment-compatible substitute exercises.

    Substitutes are ranked using:
    - Primary muscle similarity
    - TF-IDF text similarity
    - Movement family similarity
    - Exercise mechanic similarity

    Excludes existing workout exercises when
    their IDs are supplied in excluded_ids.
    """

    if excluded_ids is None:
        excluded_ids = []

    original_id = original_exercise["id"]

    # ---------------------------------
    # STEP 1: FILTER CANDIDATES
    # ---------------------------------

    candidates = filter_by_equipment(
        all_exercises,
        available_equipment,
    )

    candidates = filter_by_difficulty(
        candidates,
        experience_level,
    )

    # Match original exercise category.
    candidates = candidates[
        candidates["category"]
        == original_exercise["category"]
    ].copy()

    excluded = set(excluded_ids)
    excluded.add(original_id)

    candidates = candidates[
        ~candidates["id"].isin(excluded)
    ].copy()

    original_primary = set(
        safe_list(original_exercise["primary_muscles"])
    )

    if not original_primary:
        return pd.DataFrame()

    # Substitutes must share at least one primary muscle.
    candidates = candidates[
        candidates["primary_muscles"].apply(
            lambda muscles: bool(
                set(safe_list(muscles)) & original_primary
            )
        )
    ].copy()

    if candidates.empty:
        return candidates

    # ---------------------------------
    # STEP 2: TEXT SIMILARITY
    # ---------------------------------

    documents = [
        str(original_exercise["search_text"])
    ] + candidates["search_text"].fillna("").tolist()

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True,
    )

    vectors = vectorizer.fit_transform(documents)

    similarities = cosine_similarity(
        vectors[0:1],
        vectors[1:],
    ).flatten()

    candidates["text_similarity"] = similarities

    # ---------------------------------
    # STEP 3: MUSCLE SIMILARITY
    # ---------------------------------

    def muscle_similarity(row):
        candidate_primary = set(
            safe_list(row["primary_muscles"])
        )

        union = original_primary | candidate_primary

        if not union:
            return 0.0

        return len(
            original_primary & candidate_primary
        ) / len(union)

    candidates["muscle_similarity"] = candidates.apply(
        muscle_similarity,
        axis=1,
    )

    # ---------------------------------
    # STEP 4: MOVEMENT SIMILARITY
    # ---------------------------------

    original_family = get_exercise_family(
        original_exercise
    )

    original_group = original_exercise.get(
        "variation_group"
    )

    def movement_similarity(row):
        if (
            isinstance(original_group, str)
            and original_group.strip()
            and row.get("variation_group") == original_group
        ):
            return 1.0

        if get_exercise_family(row) == original_family:
            return 1.0

        return 0.0

    candidates["movement_similarity"] = candidates.apply(
        movement_similarity,
        axis=1,
    )

    # Match compound versus isolation movements.
    candidates["mechanic_similarity"] = candidates[
        "mechanic"
    ].apply(
        lambda value: 1.0
        if value == original_exercise["mechanic"]
        and pd.notna(value)
        else 0.0
    )

    # ---------------------------------
    # STEP 5: FINAL SUBSTITUTION SCORE
    # ---------------------------------

    candidates["substitution_score"] = (
        0.40 * candidates["muscle_similarity"]
        + 0.25 * candidates["text_similarity"]
        + 0.25 * candidates["movement_similarity"]
        + 0.10 * candidates["mechanic_similarity"]
    )

    candidates = candidates.sort_values(
        by=["substitution_score", "name"],
        ascending=[False, True],
    )

    return candidates.head(max_results).reset_index(
        drop=True
    )


# ---------------------------------
# TEST SUBSTITUTIONS
# ---------------------------------

if __name__ == "__main__":

    exercises = load_exercises()

    # Example: user loses access to a barbell
    # but has dumbbells and a bench.
    original = exercises[
        exercises["name"] == "Barbell Bench Press"
    ].iloc[0]

    replacements = get_substitutions(
        original_exercise=original,
        all_exercises=exercises,
        available_equipment=["Dumbbells", "Bench"],
        experience_level="Intermediate",
        max_results=5,
    )

    print("\nORIGINAL EXERCISE:")
    print(original["name"])
    print("Equipment:", original["equipment_name"])

    print("\nAVAILABLE EQUIPMENT:")
    print("Dumbbells, Bench")

    print("\nRECOMMENDED SUBSTITUTIONS:")

    if replacements.empty:
        print("No compatible substitutes found.")
    else:
        print(
            replacements[
                [
                    "name",
                    "equipment_name",
                    "muscle_similarity",
                    "movement_similarity",
                    "substitution_score",
                ]
            ].to_string(
                index=False,
                float_format=lambda x: f"{x:.3f}",
            )
        )
