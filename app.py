
import streamlit as st

from src.data_loader import load_exercises
from src.exercise_filter import filter_exercises


# ---------------------------------
# PAGE CONFIGURATION
# ---------------------------------

st.set_page_config(
    page_title="GymGenie",
    page_icon="💪",
    layout="wide"
)


# ---------------------------------
# LOAD EXERCISE DATASET
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
# HEADER
# ---------------------------------

st.title("💪 GymGenie")
st.subheader("Your Personalized Workout Planner")

st.write(
    "Find exercises that match your available equipment, "
    "target muscle groups, and fitness preferences."
)

st.divider()


# ---------------------------------
# WORKOUT PREFERENCES
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
        "Select the equipment you have access to:",
        equipment_options,
    )

    st.caption(
        "Leave empty for exercises that require no equipment."
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
        "Which muscle groups would you like to target?",
        muscle_options,
    )

    st.subheader("3. Experience Level")

    experience_level = st.selectbox(
        "Select your experience level:",
        ["Beginner", "Intermediate", "Advanced"],
    )

    st.subheader("4. Exercise Category")

    exercise_category = st.selectbox(
        "What type of exercise are you looking for?",
        [
            "Strength",
            "Stretching",
            "Cardio",
            "Olympic",
            "Plyometrics",
            "All Categories",
        ],
    )

    st.subheader("5. Workout Duration")

    workout_duration = st.slider(
        "How much time do you have? (minutes)",
        min_value=15,
        max_value=120,
        value=45,
        step=5,
    )

    st.subheader("6. Number of Exercises")

    num_exercises = st.slider(
        "How many exercises would you like?",
        min_value=1,
        max_value=12,
        value=5,
    )

    st.divider()

    submitted = st.form_submit_button(
        "Generate Workout",
        type="primary",
    )


# ---------------------------------
# FILTER AND DISPLAY EXERCISES
# ---------------------------------

if submitted:

    if not selected_muscles:
        st.warning(
            "Please select at least one target muscle group."
        )

    else:
        # Filter by equipment, muscles, and difficulty.
        filtered = filter_exercises(
            exercises,
            selected_equipment,
            selected_muscles,
            experience_level,
        )

        # Filter by exercise category.
        if exercise_category != "All Categories":
            filtered = filtered[
                filtered["category"]
                == exercise_category.lower()
            ].copy()

        st.divider()

        st.header("Your Exercise Recommendations")

        st.write("**Available Equipment:**",
                 ", ".join(selected_equipment)
                 if selected_equipment
                 else "Bodyweight Only")

        st.write("**Target Muscles:**",
                 ", ".join(selected_muscles))

        st.write("**Experience Level:**",
                 experience_level)

        st.write("**Category:**", exercise_category)

        st.write("**Workout Duration:**",
                 f"{workout_duration} minutes")

        st.write("**Requested Exercises:**", num_exercises)

        st.divider()

        st.write(
            f"**{len(filtered)} compatible exercises found.**"
        )

        if filtered.empty:
            st.warning(
                "No exercises match your preferences. "
                "Try selecting more equipment, changing "
                "your muscle groups, or choosing a "
                "different exercise category."
            )

        else:
            # Temporary selection: first N matching exercises.
            # Relevance ranking will be added in Phase 3.
            recommendations = filtered.head(
                num_exercises
            )

            if len(recommendations) < num_exercises:
                st.info(
                    "Fewer compatible exercises were found "
                    "than the number requested."
                )

            st.caption(
                "These are compatible exercise matches, "
                "not a fully optimized workout. "
                "Relevance ranking and workout timing "
                "will be implemented in later phases."
            )

            for index, (_, exercise) in enumerate(
                recommendations.iterrows(),
                start=1,
            ):

                with st.expander(
                    f"{index}. {exercise['name']}",
                    expanded=True,
                ):

                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(
                            "**Equipment:**",
                            exercise["equipment_name"],
                        )

                        st.write(
                            "**Difficulty:**",
                            exercise["difficulty"].title(),
                        )

                        st.write(
                            "**Category:**",
                            exercise["category"].title(),
                        )

                        additional = exercise[
                            "additional_required_equipment"
                        ]

                        if isinstance(additional, list) and additional:
                            st.write(
                                "**Additional Equipment IDs:**",
                                ", ".join(additional),
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
                    st.write(exercise["description"])

                    instructions = exercise["instructions"]

                    if isinstance(instructions, list) and instructions:
                        st.write("**Instructions:**")

                        for step_number, instruction in enumerate(
                            instructions,
                            start=1,
                        ):
                            st.write(
                                f"{step_number}. {instruction}"
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
