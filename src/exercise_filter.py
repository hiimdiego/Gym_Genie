
import pandas as pd

from data_loader import load_exercises


# ---------------------------------
# EQUIPMENT NAME MAPPING
# ---------------------------------

# Map the labels used in the Streamlit interface
# to the equipment IDs used by RepDB.

EQUIPMENT_MAP = {
    "Dumbbells": "dumbbell",
    "Barbell": "barbell",
    "Bench": "flat_bench",
    "Flat Bench": "flat_bench",
    "Incline Bench": "incline_bench",
    "Cable Machine": "cable",
    "Resistance Bands": "resistance_band",
    "Kettlebells": "kettlebell",
    "Pull-Up Bar": "pull_up_bar",
    "Smith Machine": "smith_machine",
    "Leg Press Machine": "leg_press",
    "Treadmill": "treadmill",
}


# ---------------------------------
# MUSCLE GROUP MAPPING
# ---------------------------------

# Match the user-facing muscle groups to the
# specific muscle IDs in the RepDB dataset.

MUSCLE_MAP = {
    "Chest": [
        "pectoralis_major",
        "serratus_anterior",
    ],
    "Back": [
        "latissimus_dorsi",
        "rhomboids",
        "trapezius",
        "erector_spinae",
        "quadratus_lumborum",
    ],
    "Shoulders": [
        "anterior_deltoid",
        "lateral_deltoid",
        "posterior_deltoid",
        "supraspinatus",
        "infraspinatus_teres_minor",
    ],
    "Biceps": [
        "biceps_brachii",
        "brachialis",
        "brachioradialis",
    ],
    "Triceps": [
        "triceps_brachii",
    ],
    "Quadriceps": [
        "quadriceps",
    ],
    "Hamstrings": [
        "hamstrings",
    ],
    "Glutes": [
        "gluteus_maximus",
        "gluteus_medius",
    ],
    "Calves": [
        "gastrocnemius",
        "soleus",
    ],
    "Core": [
        "rectus_abdominis",
        "obliques",
        "transverse_abdominis",
        "hip_flexors",
    ],
}


# ---------------------------------
# EXPERIENCE LEVELS
# ---------------------------------

DIFFICULTY_LEVELS = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
}


# ---------------------------------
# HELPER FUNCTIONS
# ---------------------------------

def safe_list(value):
    """Return a list, even when a dataset value is missing."""

    if isinstance(value, list):
        return value

    return []


def normalize_equipment(selected_equipment):
    """Convert UI equipment names into RepDB IDs."""

    normalized = set()

    for item in selected_equipment:
        if item in EQUIPMENT_MAP:
            normalized.add(EQUIPMENT_MAP[item])
        else:
            # Also support raw RepDB IDs.
            normalized.add(item)

    return normalized


# ---------------------------------
# FILTER BY EQUIPMENT
# ---------------------------------

def filter_by_equipment(exercises, selected_equipment):
    """
    Keep exercises that can be performed using
    the user's available equipment.

    Exercises with no required equipment are allowed.
    """

    available = normalize_equipment(selected_equipment)

    def equipment_matches(row):

        primary_equipment = row["equipment"]

        additional_equipment = safe_list(
            row["additional_required_equipment"]
        )

        required = set(additional_equipment)

        if pd.notna(primary_equipment):
            required.add(primary_equipment)

        return required.issubset(available)

    return exercises[
        exercises.apply(equipment_matches, axis=1)
    ].copy()


# ---------------------------------
# FILTER BY MUSCLE GROUP
# ---------------------------------

def filter_by_muscles(exercises, selected_muscles):
    """
    Keep exercises that target at least one
    of the user's selected muscle groups.
    """

    target_muscles = set()

    for muscle in selected_muscles:
        target_muscles.update(
            MUSCLE_MAP.get(muscle, [muscle])
        )

    if not target_muscles:
        return exercises.iloc[0:0].copy()

    def muscle_matches(row):

        primary = set(
            safe_list(row["primary_muscles"])
        )

        secondary = set(
            safe_list(row["secondary_muscles"])
        )

        exercise_muscles = primary | secondary

        return bool(
            exercise_muscles.intersection(target_muscles)
        )

    return exercises[
        exercises.apply(muscle_matches, axis=1)
    ].copy()


# ---------------------------------
# FILTER BY EXPERIENCE LEVEL
# ---------------------------------

def filter_by_difficulty(exercises, experience_level):
    """
    Remove exercises above the user's level.

    Beginner: beginner exercises
    Intermediate: beginner + intermediate
    Advanced: all levels
    """

    user_level = DIFFICULTY_LEVELS[
        experience_level.lower()
    ]

    return exercises[
        exercises["difficulty"].apply(
            lambda difficulty:
                DIFFICULTY_LEVELS.get(difficulty, 99)
                <= user_level
        )
    ].copy()


# ---------------------------------
# COMBINE ALL FILTERS
# ---------------------------------

def filter_exercises(
    exercises,
    selected_equipment,
    selected_muscles,
    experience_level,
):
    """
    Apply the equipment, muscle group, and
    experience-level filters.
    """

    filtered = filter_by_equipment(
        exercises,
        selected_equipment
    )

    filtered = filter_by_muscles(
        filtered,
        selected_muscles
    )

    filtered = filter_by_difficulty(
        filtered,
        experience_level
    )

    return filtered.reset_index(drop=True)


# ---------------------------------
# TEST FILTERING
# ---------------------------------

if __name__ == "__main__":

    print("\nLoading GymGenie exercise dataset...")

    exercises = load_exercises()

    # Example user preferences
    selected_equipment = [
        "Dumbbells",
        "Bench",
    ]

    selected_muscles = [
        "Chest",
        "Triceps",
    ]

    experience_level = "Beginner"

    print(f"\nTotal exercises: {len(exercises)}")

    print("\nUser preferences:")
    print("Equipment:", selected_equipment)
    print("Muscles:", selected_muscles)
    print("Experience:", experience_level)

    # Apply all filters
    filtered = filter_exercises(
        exercises,
        selected_equipment,
        selected_muscles,
        experience_level,
    )

    print(f"\nMatching exercises: {len(filtered)}")

    if filtered.empty:
        print("\nNo matching exercises found.")

    else:
        print("\nMatching exercise examples:")

        print(
            filtered[
                [
                    "name",
                    "equipment_name",
                    "difficulty",
                ]
            ].head(20).to_string(index=False)
        )

    print("\nFiltering completed successfully!")
