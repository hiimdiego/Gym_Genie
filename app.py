
import streamlit as st

from src.data_loader import load_exercises
from src.exercise_filter import (
    filter_exercises,
    filter_by_equipment,
)
from src.ranking import rank_exercises
from src.substitutions import get_substitutions
from src.workout import (
    generate_workout,
    get_prescription,
    estimate_exercise_seconds,
    WARMUP_MINUTES,
)


# ---------------------------------
# PAGE CONFIGURATION AND DATA
# ---------------------------------

st.set_page_config(
    page_title="GymGenie",
    page_icon="💪",
    layout="wide",
)


@st.cache_data
def get_exercises():
    return load_exercises()


try:
    exercises = get_exercises()
except (FileNotFoundError, KeyError, ValueError) as error:
    st.error(f"Unable to load dataset: {error}")
    st.stop()


EQUIPMENT_OPTIONS = [
    "Dumbbells",
    "Barbell",
    "Bench",
    "Cable Machine",
    "Resistance Bands",
    "Kettlebells",
    "Pull-Up Bar",
    "Smith Machine",
    "Leg Press Machine",
    "Treadmill",
]

MUSCLE_OPTIONS = [
    "Chest",
    "Back",
    "Shoulders",
    "Biceps",
    "Triceps",
    "Quadriceps",
    "Hamstrings",
    "Glutes",
    "Calves",
    "Core",
]


# ---------------------------------
# SESSION STATE
# ---------------------------------

if "workout" not in st.session_state:
    st.session_state.workout = None

if "workout_preferences" not in st.session_state:
    st.session_state.workout_preferences = None

if "ranked_results" not in st.session_state:
    st.session_state.ranked_results = None


# ---------------------------------
# HELPER FUNCTIONS
# ---------------------------------

def calculate_workout_time(workout, preferences):
    """Recalculate estimated time including warm-up."""

    total_seconds = WARMUP_MINUTES * 60

    for _, exercise in workout.iterrows():
        prescription = get_prescription(
            exercise,
            preferences["experience"],
            preferences["duration"],
        )

        total_seconds += estimate_exercise_seconds(
            prescription
        )

    return round(total_seconds / 60, 1)


def display_exercise(exercise, index, workout_mode=False):
    """Display exercise details and instructions."""

    with st.expander(
        f"{index}. {exercise['name']}",
        expanded=True,
    ):

        if workout_mode:

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Sets", int(exercise["sets"]))

            with col2:
                label = (
                    "Hold Duration"
                    if exercise["prescription_type"] == "hold"
                    else "Reps"
                )
                st.metric(label, exercise["reps"])

            with col3:
                st.metric(
                    "Rest",
                    f"{int(exercise['rest_seconds'])} sec",
                )

            st.caption(
                f"Estimated exercise time: "
                f"{exercise['estimated_minutes']:.1f} min"
            )

        if "relevance_score" in exercise.index:
            st.write(
                "**Relevance Score:**",
                f"{exercise['relevance_score']:.3f}",
            )

        if (
            "muscle_score" in exercise.index
            and "tfidf_score" in exercise.index
        ):
            with st.expander("View Ranking Details"):
                st.write(
                    "**Muscle Score:**",
                    f"{exercise['muscle_score']:.3f}",
                )
                st.write(
                    "**TF-IDF Score:**",
                    f"{exercise['tfidf_score']:.3f}",
                )

        col1, col2 = st.columns(2)

        with col1:
            st.write(
                "**Equipment:**",
                exercise["equipment_name"],
            )
            additional = exercise.get(
                "additional_required_equipment"
            )
            if isinstance(additional, list) and additional:
                st.write(
                    "**Additional Equipment IDs:**",
                    ", ".join(additional),
                )
            st.write(
                "**Difficulty:**",
                exercise["difficulty"].title(),
            )

        with col2:
            st.write("**Primary Muscles:**")
            st.write(
                ", ".join(
                    exercise["primary_muscle_names"]
                ) or "Not specified"
            )

            st.write("**Secondary Muscles:**")
            st.write(
                ", ".join(
                    exercise["secondary_muscle_names"]
                ) or "Not specified"
            )

        st.write("**Description:**")
        st.write(
            exercise["description"]
            or "No description available."
        )

        instructions = exercise["instructions"]

        if isinstance(instructions, list) and instructions:
            st.write("**Instructions:**")
            for number, instruction in enumerate(
                instructions,
                start=1,
            ):
                st.write(f"{number}. {instruction}")

        tips = exercise["tips"]

        if isinstance(tips, list) and tips:
            with st.expander("Exercise Tips"):
                for tip in tips:
                    st.write(f"- {tip}")


# ---------------------------------
# HEADER
# ---------------------------------

st.title("💪 GymGenie")
st.subheader("Your Personalized Workout Planner")

st.write(
    "Create personalized, equipment-aware workouts "
    "using exercise retrieval and ranking."
)

st.divider()


# ---------------------------------
# WORKOUT FORM
# ---------------------------------

st.header("Customize Your Workout")

with st.form("workout_form"):

    st.subheader("1. Available Equipment")

    selected_equipment = st.multiselect(
        "Select your available equipment:",
        EQUIPMENT_OPTIONS,
    )

    st.caption(
        "Leave empty for exercises requiring no equipment."
    )

    st.subheader("2. Target Muscle Groups")

    selected_muscles = st.multiselect(
        "Choose your target muscles:",
        MUSCLE_OPTIONS,
    )

    st.subheader("3. Experience Level")

    experience_level = st.selectbox(
        "Experience level:",
        ["Beginner", "Intermediate", "Advanced"],
    )

    st.subheader("4. Exercise Category")

    exercise_category = st.selectbox(
        "Exercise category:",
        [
            "Strength",
            "Stretching",
            "Cardio",
            "Olympic",
            "Plyometrics",
            "All Categories",
        ],
    )

    st.subheader("5. Recommendation Method")

    ranking_method = st.selectbox(
        "Ranking algorithm:",
        ["Hybrid", "Rule-Based", "TF-IDF"],
    )

    st.subheader("6. Workout Duration")

    workout_duration = st.slider(
        "Available time (minutes):",
        min_value=15,
        max_value=120,
        value=45,
        step=5,
    )

    st.subheader("7. Number of Exercises")

    num_exercises = st.slider(
        "Desired number of exercises:",
        min_value=1,
        max_value=12,
        value=5,
    )

    submitted = st.form_submit_button(
        "Generate Workout",
        type="primary",
        use_container_width=True,
    )


# ---------------------------------
# GENERATE RESULTS
# ---------------------------------

if submitted:

    if not selected_muscles:
        st.warning("Please select at least one muscle group.")

    else:
        filtered = filter_exercises(
            exercises,
            selected_equipment,
            selected_muscles,
            experience_level,
        )

        if exercise_category != "All Categories":
            filtered = filtered[
                filtered["category"]
                == exercise_category.lower()
            ].copy()

        ranked = rank_exercises(
            all_exercises=exercises,
            filtered_exercises=filtered,
            selected_muscles=selected_muscles,
            method=ranking_method,
        )

        preferences = {
            "equipment": selected_equipment,
            "muscles": selected_muscles,
            "experience": experience_level,
            "category": exercise_category,
            "ranking": ranking_method,
            "duration": workout_duration,
            "count": num_exercises,
        }

        st.session_state.workout_preferences = preferences
        st.session_state.ranked_results = ranked
        st.session_state.workout = None
        st.session_state.replacement_equipment = (
            selected_equipment.copy()
        )

        if exercise_category == "Strength":

            workout, _ = generate_workout(
                ranked_exercises=ranked,
                selected_muscles=selected_muscles,
                selected_equipment=selected_equipment,
                experience_level=experience_level,
                duration=workout_duration,
                num_exercises=num_exercises,
            )

            st.session_state.workout = workout


# ---------------------------------
# DISPLAY PERSISTENT RESULTS
# ---------------------------------

preferences = st.session_state.workout_preferences

if preferences is not None:

    st.divider()
    st.header("Your Results")

    st.write(
        "**Equipment:**",
        ", ".join(preferences["equipment"])
        or "Bodyweight Only",
    )

    st.write(
        "**Target Muscles:**",
        ", ".join(preferences["muscles"]),
    )

    st.write(
        "**Experience Level:**",
        preferences["experience"],
    )

    st.write(
        "**Ranking Method:**",
        preferences["ranking"],
    )

    ranked = st.session_state.ranked_results

    st.write(
        f"**Compatible exercises found:** {len(ranked)}"
    )

    if ranked.empty:
        st.warning("No compatible exercises found.")

    # ---------------------------------
    # STRUCTURED STRENGTH WORKOUT
    # ---------------------------------

    elif preferences["category"] == "Strength":

        workout = st.session_state.workout

        if workout is None or workout.empty:
            st.warning(
                "No feasible workout could be assembled."
            )

        else:
            st.subheader("Your Personalized Workout")

            total_time = calculate_workout_time(
                workout,
                preferences,
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Exercises", len(workout))

            with col2:
                st.metric(
                    "Estimated Duration",
                    f"{total_time:.1f} min",
                )

            with col3:
                st.metric(
                    "Time Limit",
                    f"{preferences['duration']} min",
                )

            st.caption(
                f"Includes an estimated "
                f"{WARMUP_MINUTES}-minute warm-up."
            )

            if len(workout) < preferences["count"]:
                st.info(
                    "Fewer exercises were selected because "
                    "of time, variety, or available options."
                )

            st.divider()

            # ---------------------------------
            # EQUIPMENT FOR SUBSTITUTIONS
            # ---------------------------------

            st.subheader("Exercise Substitutions")

            st.write(
                "Changed gyms or lost access to equipment? "
                "Update your available equipment below, "
                "then choose replacement exercises."
            )

            replacement_equipment = st.multiselect(
                "Equipment currently available:",
                EQUIPMENT_OPTIONS,
                key="replacement_equipment",
            )

            compatible = filter_by_equipment(
                workout,
                replacement_equipment,
            )

            incompatible_ids = (
                set(workout["id"])
                - set(compatible["id"])
            )

            if incompatible_ids:
                st.warning(
                    f"{len(incompatible_ids)} exercise(s) "
                    "in your workout require equipment "
                    "you no longer have."
                )
            else:
                st.success(
                    "All current exercises are compatible "
                    "with your available equipment."
                )

            st.divider()

            # ---------------------------------
            # DISPLAY WORKOUT + REPLACEMENTS
            # ---------------------------------

            for index, (_, exercise) in enumerate(
                workout.iterrows(),
                start=1,
            ):

                display_exercise(
                    exercise,
                    index,
                    workout_mode=True,
                )

                exercise_id = exercise["id"]

                if exercise_id in incompatible_ids:
                    st.warning(
                        "This exercise requires unavailable "
                        "equipment. Choose a substitute."
                    )

                with st.expander(
                    f"Replace {exercise['name']}"
                ):

                    other_ids = [
                        item_id
                        for item_id in workout["id"].tolist()
                        if item_id != exercise_id
                    ]

                    alternatives = get_substitutions(
                        original_exercise=exercise,
                        all_exercises=exercises,
                        available_equipment=replacement_equipment,
                        experience_level=preferences["experience"],
                        excluded_ids=other_ids,
                        max_results=5,
                    )

                    if alternatives.empty:
                        st.info(
                            "No compatible substitutes found. "
                            "Try selecting more equipment."
                        )

                    else:
                        alternatives_by_id = {
                            row["id"]: row
                            for _, row in alternatives.iterrows()
                        }

                        selected_id = st.selectbox(
                            "Choose a replacement:",
                            options=list(
                                alternatives_by_id.keys()
                            ),
                            format_func=lambda item_id: (
                                alternatives_by_id[item_id]["name"]
                            ),
                            key=f"substitute_{exercise_id}",
                        )

                        replacement = alternatives_by_id[
                            selected_id
                        ]

                        st.write(
                            "**Substitution Score:**",
                            f"{replacement['substitution_score']:.3f}",
                        )

                        st.write(
                            "**Equipment:**",
                            replacement["equipment_name"],
                        )

                        st.write(
                            "**Primary Muscles:**",
                            ", ".join(
                                replacement["primary_muscle_names"]
                            ),
                        )

                        if st.button(
                            "Replace Exercise",
                            key=f"replace_{exercise_id}",
                        ):

                            prescription = get_prescription(
                                replacement,
                                preferences["experience"],
                                preferences["duration"],
                            )

                            new_row = replacement.copy()

                            new_row["sets"] = (
                                prescription["sets"]
                            )

                            new_row["reps"] = (
                                prescription["reps"]
                            )

                            new_row["rest_seconds"] = (
                                prescription["rest_seconds"]
                            )

                            new_row["prescription_type"] = (
                                prescription["prescription_type"]
                            )

                            new_row["estimated_minutes"] = round(
                                estimate_exercise_seconds(
                                    prescription
                                ) / 60,
                                1,
                            )

                            # Preserve the current workout's
                            # retrieval scores for replacement display.
                            matching_rank = ranked[
                                ranked["id"] == selected_id
                            ]

                            for score_column in [
                                "relevance_score",
                                "muscle_score",
                                "tfidf_score",
                            ]:
                                if not matching_rank.empty:
                                    new_row[score_column] = (
                                        matching_rank.iloc[0][
                                            score_column
                                        ]
                                    )
                                else:
                                    new_row[score_column] = 0.0

                            updated = workout.copy()

                            for column in new_row.index:
                                if column not in updated.columns:
                                    updated[column] = None

                            for column in updated.columns:
                                if column in new_row.index:
                                    updated.at[
                                        index - 1, column
                                    ] = new_row[column]

                            new_duration = calculate_workout_time(
                                updated,
                                preferences,
                            )

                            if (
                                new_duration
                                > preferences["duration"]
                            ):
                                st.error(
                                    "This replacement would exceed "
                                    "your workout time limit."
                                )
                            else:
                                st.session_state.workout = updated
                                st.rerun()

            # ---------------------------------
            # WORKOUT SUMMARY
            # ---------------------------------

            st.divider()
            st.subheader("Workout Summary")

            summary = workout[
                [
                    "name",
                    "equipment_name",
                    "sets",
                    "reps",
                    "rest_seconds",
                    "estimated_minutes",
                ]
            ].copy()

            summary.columns = [
                "Exercise",
                "Equipment",
                "Sets",
                "Reps / Hold",
                "Rest (sec)",
                "Estimated Time (min)",
            ]

            st.dataframe(
                summary,
                use_container_width=True,
                hide_index=True,
            )

    # ---------------------------------
    # OTHER CATEGORIES
    # ---------------------------------

    else:
        st.subheader("Ranked Exercise Recommendations")

        st.caption(
            "Structured workout generation and "
            "substitutions are currently available "
            "for strength workouts."
        )

        for index, (_, exercise) in enumerate(
            ranked.head(preferences["count"]).iterrows(),
            start=1,
        ):
            display_exercise(exercise, index)


# ---------------------------------
# FOOTER
# ---------------------------------

st.divider()

st.caption(
    "GymGenie | CS 410: Text Information Systems"
)

st.markdown(
    "Exercise data by [RepDB](https://repdb.co)"
)
