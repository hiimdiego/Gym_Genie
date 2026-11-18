
import re

import pandas as pd

from src.exercise_filter import MUSCLE_MAP, normalize_equipment


# ---------------------------------
# WORKOUT CONFIGURATION
# ---------------------------------

WARMUP_MINUTES = 5
TRANSITION_SECONDS = 60

REST_SECONDS = {
    "beginner": 60,
    "intermediate": 75,
    "advanced": 90,
}

# Approximate time spent performing one set
DYNAMIC_SET_SECONDS = 45

# Approximate hold duration for static exercises
STATIC_HOLD_SECONDS = {
    "beginner": 20,
    "intermediate": 30,
    "advanced": 40,
}


# ---------------------------------
# HELPER FUNCTIONS
# ---------------------------------

def safe_list(value):
    """Return a list when a field is missing."""
    return value if isinstance(value, list) else []


def get_muscle_matches(exercise, selected_muscles):
    """
    Match requested muscle groups against an exercise.

    Primary match: 1.0
    Secondary match: 0.35
    No match: 0.0
    """

    primary = set(safe_list(exercise["primary_muscles"]))
    secondary = set(safe_list(exercise["secondary_muscles"]))

    matches = {}

    for group in selected_muscles:
        targets = set(MUSCLE_MAP.get(group, [group]))

        if primary & targets:
            matches[group] = 1.0

        elif secondary & targets:
            matches[group] = 0.35

    return matches


def get_exercise_family(exercise):
    """
    Identify closely related exercises.

    Uses RepDB variation groups when available,
    plus fallback rules for missing groups.
    """

    name = str(exercise["name"]).lower().strip()
    group = exercise.get("variation_group")

    # Known related movements with incomplete grouping
    if "svend press" in name:
        return "svend-press"

    # Use explicitly defined variation groups.
    if isinstance(group, str) and group.strip():

        # "static-hold" is too broad to represent
        # one movement family.
        if group.strip() != "static-hold":
            return group.strip()

    # Normalize common exercise-name variations.
    normalized = re.sub(
        r"\b(single.arm|single|one.arm|seated|standing|"
        r"alternating|dumbbell|barbell|kettlebell|"
        r"bodyweight|weighted)\b",
        "",
        name,
    )

    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized or str(exercise["id"])


def is_static_exercise(exercise):
    """Identify static holds using RepDB metadata."""
    return str(exercise.get("force_type", "")).lower() == "static"


def get_prescription(exercise, experience_level, duration):
    """
    Determine sets, reps/hold duration, and rest.

    Static exercises use seconds.
    Dynamic exercises use repetitions.
    """

    level = experience_level.lower()

    sets = 2 if duration <= 30 else 3
    rest = REST_SECONDS.get(level, 75)

    if is_static_exercise(exercise):

        hold_seconds = STATIC_HOLD_SECONDS.get(level, 30)

        prescription = f"{hold_seconds} sec"
        set_seconds = hold_seconds
        prescription_type = "hold"

    else:

        prescription = {
            "beginner": "8-12",
            "intermediate": "8-12",
            "advanced": "6-12",
        }.get(level, "8-12")

        set_seconds = DYNAMIC_SET_SECONDS
        prescription_type = "reps"

    return {
        "sets": sets,
        "reps": prescription,
        "rest_seconds": rest,
        "set_seconds": set_seconds,
        "prescription_type": prescription_type,
    }


def estimate_exercise_seconds(prescription):
    """Estimate working time, rest, and transition."""

    sets = prescription["sets"]
    rest = prescription["rest_seconds"]
    set_seconds = prescription["set_seconds"]

    working_time = sets * set_seconds
    resting_time = max(sets - 1, 0) * rest

    return (
        working_time
        + resting_time
        + TRANSITION_SECONDS
    )


# ---------------------------------
# EXERCISE SELECTION SCORING
# ---------------------------------

def calculate_selection_score(
    exercise,
    selected_muscles,
    coverage,
    selected_rows,
    available_equipment,
):
    """
    Score an exercise for inclusion in a workout.

    Combines:
    - Existing relevance ranking
    - Primary muscle relevance
    - Coverage of underserved muscles
    - Exercise diversity
    - Available equipment utilization
    """

    score = float(exercise["relevance_score"])

    matches = get_muscle_matches(
        exercise,
        selected_muscles,
    )

    # Strong preference for direct muscle matches.
    primary_matches = sum(
        value == 1.0
        for value in matches.values()
    )

    if selected_muscles:
        score += (
            0.25 * primary_matches / len(selected_muscles)
        )

    # Reward exercises that directly target muscles
    # which have not yet received primary coverage.
    for muscle, strength in matches.items():

        if coverage[muscle] == 0:
            if strength == 1.0:
                score += 0.65
            else:
                score += 0.10

        elif coverage[muscle] < 1.0:
            score += 0.15 * strength

        else:
            score += 0.08 * strength / (
                1.0 + coverage[muscle]
            )

    # Slight preference for using owned equipment.
    equipment_id = exercise.get("equipment")

    if (
        isinstance(equipment_id, str)
        and equipment_id in available_equipment
    ):
        score += 0.08

    # Penalize highly overlapping primary muscles.
    current_primary = set(
        safe_list(exercise["primary_muscles"])
    )

    for chosen in selected_rows:

        chosen_primary = set(
            safe_list(chosen["primary_muscles"])
        )

        if current_primary and chosen_primary:

            overlap = len(
                current_primary & chosen_primary
            ) / len(
                current_primary | chosen_primary
            )

            score -= 0.18 * overlap

    return score


# ---------------------------------
# GENERATE WORKOUT
# ---------------------------------

def generate_workout(
    ranked_exercises,
    selected_muscles,
    selected_equipment,
    experience_level,
    duration,
    num_exercises,
):
    """
    Generate a balanced strength workout.

    The algorithm:
    1. Uses ranked compatible exercises.
    2. Avoids repeated exercise families.
    3. Prioritizes requested muscle groups.
    4. Balances muscle coverage.
    5. Assigns sets, reps, or static hold times.
    6. Keeps estimated duration within the limit.

    Returns:
        workout DataFrame
        estimated total minutes
    """

    empty_result = (pd.DataFrame(), 0.0)

    if ranked_exercises.empty:
        return empty_result

    if not selected_muscles:
        return empty_result

    if duration <= WARMUP_MINUTES or num_exercises <= 0:
        return empty_result

    # Only generate structured strength workouts.
    candidates = ranked_exercises[
        ranked_exercises["category"] == "strength"
    ].copy()

    if candidates.empty:
        return empty_result

    available_equipment = normalize_equipment(
        selected_equipment
    )

    max_seconds = duration * 60
    total_seconds = WARMUP_MINUTES * 60

    selected_rows = []
    used_ids = set()
    used_families = set()

    # Track muscle coverage using primary/secondary
    # match strengths.
    coverage = {
        muscle: 0.0
        for muscle in selected_muscles
    }

    while len(selected_rows) < num_exercises:

        best_index = None
        best_score = float("-inf")
        best_prescription = None
        best_seconds = None

        for index, exercise in candidates.iterrows():

            exercise_id = exercise["id"]
            family = get_exercise_family(exercise)

            # Prefer exercises that directly target
            # at least one requested muscle group.
            matches = get_muscle_matches(
                exercise,
                selected_muscles,
            )

            has_primary_match = any(
                strength == 1.0
                for strength in matches.values()
            )

            # Exclude secondary-only matches when enough
            # primary-targeting exercises are available.
            if not has_primary_match:
                continue


            # Avoid duplicate exercises.
            if exercise_id in used_ids:
                continue

            # Avoid closely related variations.
            if family in used_families:
                continue

            prescription = get_prescription(
                exercise,
                experience_level,
                duration,
            )

            exercise_seconds = estimate_exercise_seconds(
                prescription
            )

            # Enforce estimated workout time.
            if (
                total_seconds + exercise_seconds
                > max_seconds
            ):
                continue

            selection_score = calculate_selection_score(
                exercise,
                selected_muscles,
                coverage,
                selected_rows,
                available_equipment,
            )

            if selection_score > best_score:

                best_score = selection_score
                best_index = index
                best_prescription = prescription
                best_seconds = exercise_seconds

        # No additional feasible exercises.
        if best_index is None:
            break

        chosen = candidates.loc[best_index].copy()

        # Attach workout prescription.
        chosen["sets"] = best_prescription["sets"]
        chosen["reps"] = best_prescription["reps"]

        chosen["rest_seconds"] = (
            best_prescription["rest_seconds"]
        )

        chosen["prescription_type"] = (
            best_prescription["prescription_type"]
        )

        chosen["estimated_minutes"] = round(
            best_seconds / 60,
            1,
        )

        chosen["selection_score"] = best_score

        selected_rows.append(chosen)

        used_ids.add(chosen["id"])
        used_families.add(get_exercise_family(chosen))

        matches = get_muscle_matches(
            chosen,
            selected_muscles,
        )

        for muscle, strength in matches.items():
            coverage[muscle] += strength

        total_seconds += best_seconds

    if not selected_rows:
        return empty_result

    workout = pd.DataFrame(
        selected_rows
    ).reset_index(drop=True)

    estimated_total = round(total_seconds / 60, 1)

    return workout, estimated_total


# ---------------------------------
# TEST WORKOUT GENERATION
# ---------------------------------

if __name__ == "__main__":

    from src.data_loader import load_exercises
    from src.exercise_filter import filter_exercises
    from src.ranking import rank_exercises

    exercises = load_exercises()

    test_cases = [
        {
            "name": "Beginner Chest and Triceps",
            "equipment": ["Dumbbells", "Bench"],
            "muscles": ["Chest", "Triceps"],
            "level": "Beginner",
            "duration": 45,
            "count": 5,
        },
        {
            "name": "Short Biceps and Triceps",
            "equipment": ["Dumbbells"],
            "muscles": ["Biceps", "Triceps"],
            "level": "Beginner",
            "duration": 15,
            "count": 8,
        },
        {
            "name": "Bodyweight Chest and Core",
            "equipment": [],
            "muscles": ["Chest", "Core"],
            "level": "Intermediate",
            "duration": 30,
            "count": 4,
        },
    ]

    for test in test_cases:

        print("\n" + "=" * 55)
        print(test["name"])
        print("=" * 55)

        filtered = filter_exercises(
            exercises,
            test["equipment"],
            test["muscles"],
            test["level"],
        )

        filtered = filtered[
            filtered["category"] == "strength"
        ].copy()

        ranked = rank_exercises(
            all_exercises=exercises,
            filtered_exercises=filtered,
            selected_muscles=test["muscles"],
            method="Hybrid",
        )

        workout, total_minutes = generate_workout(
            ranked_exercises=ranked,
            selected_muscles=test["muscles"],
            selected_equipment=test["equipment"],
            experience_level=test["level"],
            duration=test["duration"],
            num_exercises=test["count"],
        )

        if workout.empty:
            print("No feasible workout found.")
            continue

        print(
            workout[
                [
                    "name",
                    "equipment_name",
                    "sets",
                    "reps",
                    "prescription_type",
                    "estimated_minutes",
                ]
            ].to_string(index=False)
        )

        print(f"\nExercises: {len(workout)}")
        print(f"Estimated time: {total_minutes} min")
        print(f"Time limit: {test['duration']} min")

        # Check basic constraints.
        assert total_minutes <= test["duration"]
        assert len(workout) <= test["count"]

        # Check that selected movement families are unique.
        families = [
            get_exercise_family(row)
            for _, row in workout.iterrows()
        ]

        assert len(families) == len(set(families))

        # Check static exercises have hold prescriptions.
        for _, exercise in workout.iterrows():

            if is_static_exercise(exercise):
                assert exercise["prescription_type"] == "hold"
                assert exercise["reps"].endswith("sec")

        print("\nTest passed!")

    print("\nAll workout tests completed!")
