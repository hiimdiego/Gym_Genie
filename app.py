
import streamlit as st

from src.data_loader import load_exercises
from src.exercise_filter import filter_exercises
from src.ranking import rank_exercises
from src.workout import generate_workout, WARMUP_MINUTES


# ---------------------------------
# PAGE CONFIGURATION
# ---------------------------------

st.set_page_config(
    page_title="GymGenie",
    page_icon="💪",
    layout="wide"
)


# ---------------------------------
# LOAD DATA
# ---------------------------------

@st.cache_data
def get_exercises():
    return load_exercises()


try:
    exercises = get_exercises()

except (FileNotFoundError, KeyError, ValueError) as error:
    st.error(f"Unable to load exercise dataset: {error}")
    st.stop()


# ---------------------------------
# HELPER: DISPLAY EXERCISE
# ---------------------------------

def display_exercise(exercise, index, is_workout=False):

    with st.expander(
        f"{index}. {exercise['name']}",
        expanded=True,
    ):

        if is_workout:

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Sets",
                    int(exercise["sets"]),
                )

            
            with col2:
                prescription_label = (
                    "Hold Duration"
                    if exercise["prescription_type"] == "hold"
                    else "Reps"
                )

                st.metric(
                    prescription_label,
                    exercise["reps"],
                )


            with col3:
                st.metric(
                    "Rest",
                    f"{int(exercise['rest_seconds'])} sec",
                )

            st.caption(
                f"Estimated exercise time: "
                f"{exercise['estimated_minutes']:.1f} min"
            )

        st.write(
            "**Relevance Score:**",
            f"{exercise['relevance_score']:.3f}",
        )

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

            st.write("**Equipment:**")
            st.write(exercise["equipment_name"])

            additional = exercise[
                "additional_required_equipment"
            ]

            if isinstance(additional, list) and additional:
                st.write("**Additional Equipment IDs:**")
                st.write(", ".join(additional))

            st.write("**Difficulty:**")
            st.write(exercise["difficulty"].title())

            st.write("**Category:**")
            st.write(exercise["category"].title())

        with col2:

            st.write("**Primary Muscles:**")
            st.write(
                ", ".join(exercise["primary_muscle_names"])
                or "Not specified"
            )

            st.write("**Secondary Muscles:**")
            st.write(
                ", ".join(exercise["secondary_muscle_names"])
                or "Not specified"
            )

        st.divider()

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
    "Generate equipment-aware workouts tailored "
    "to your fitness preferences."
)

st.divider()


# ---------------------------------
# WORKOUT FORM
# ---------------------------------

st.header("Customize Your Workout")

with st.form("workout_form"):

    st.subheader("1. Available Equipment")

    equipment_options = [
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

    selected_equipment = st.multiselect(
        "Select your available equipment:",
        equipment_options,
    )

    st.caption(
        "Leave empty for exercises requiring no equipment."
    )

    st.subheader("2. Target Muscle Groups")

    muscle_options = [
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

    selected_muscles = st.multiselect(
        "Which muscles would you like to target?",
        muscle_options,
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
# FILTER AND RANK
# ---------------------------------

if submitted:

    if not selected_muscles:

        st.warning(
            "Please select at least one muscle group."
        )

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

        st.divider()

        st.header("Your Results")

        # ---------------------------------
        # PREFERENCE SUMMARY
        # ---------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(
                "**Equipment:**",
                ", ".join(selected_equipment)
                or "Bodyweight Only",
            )

            st.write(
                "**Muscles:**",
                ", ".join(selected_muscles),
            )

        with col2:
            st.write(
                "**Experience:**",
                experience_level,
            )

            st.write(
                "**Category:**",
                exercise_category,
            )

        with col3:
            st.write(
                "**Duration:**",
                f"{workout_duration} min",
            )

            st.write(
                "**Ranking:**",
                ranking_method,
            )

        st.write(
            f"**Compatible exercises found:** {len(filtered)}"
        )

        st.divider()

        if ranked.empty:

            st.warning(
                "No compatible exercises found. "
                "Try different equipment or muscle groups."
            )

        # ---------------------------------
        # STRENGTH WORKOUT GENERATION
        # ---------------------------------

        elif exercise_category == "Strength":

            workout, estimated_time = generate_workout(
                ranked_exercises=ranked,
                selected_muscles=selected_muscles,
                selected_equipment=selected_equipment,
                experience_level=experience_level,
                duration=workout_duration,
                num_exercises=num_exercises,
            )

            if workout.empty:

                st.warning(
                    "Unable to assemble a workout within "
                    "your time and exercise constraints."
                )

            else:

                st.subheader("Your Personalized Workout")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Exercises",
                        len(workout),
                    )

                with col2:
                    st.metric(
                        "Estimated Duration",
                        f"{estimated_time:.1f} min",
                    )

                with col3:
                    st.metric(
                        "Time Limit",
                        f"{workout_duration} min",
                    )

                st.info(
                    f"Includes an estimated "
                    f"{WARMUP_MINUTES}-minute warm-up. "
                    "Workout time is approximate."
                )

                if len(workout) < num_exercises:

                    st.warning(
                        "GymGenie selected fewer exercises "
                        "than requested because of the time "
                        "limit or available exercise options."
                    )

                for index, (_, exercise) in enumerate(
                    workout.iterrows(),
                    start=1,
                ):
                    display_exercise(
                        exercise,
                        index,
                        is_workout=True,
                    )

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
                    "Reps",
                    "Rest (sec)",
                    "Estimated Time (min)",
                ]

                st.dataframe(
                    summary,
                    use_container_width=True,
                    hide_index=True,
                )

                st.caption(
                    "Exercises are selected using "
                    f"{ranking_method} relevance ranking "
                    "with additional muscle coverage "
                    "and exercise-variety considerations. "
                    "Sets, repetitions, and times are "
                    "general estimates."
                )

        # ---------------------------------
        # OTHER EXERCISE CATEGORIES
        # ---------------------------------

        else:

            st.subheader("Ranked Exercise Recommendations")

            recommendations = ranked.head(num_exercises)

            st.caption(
                "These are ranked exercise matches. "
                "Structured workout generation is "
                "currently implemented for strength "
                "training only."
            )

            for index, (_, exercise) in enumerate(
                recommendations.iterrows(),
                start=1,
            ):

                display_exercise(
                    exercise,
                    index,
                    is_workout=False,
                )


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
