
import streamlit as st

from src.data_loader import load_exercises
from src.exercise_filter import filter_exercises
from src.ranking import rank_exercises


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
    """Load and cache the exercise dataset."""
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
    "target muscle groups, experience level, and fitness preferences."
)

st.divider()


# ---------------------------------
# WORKOUT PREFERENCES
# ---------------------------------

st.header("Customize Your Workout")

with st.form("workout_form"):

    # Equipment selection
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
        "Select the equipment you currently have access to:",
        options=equipment_options,
        placeholder="Choose available equipment...",
    )

    st.caption(
        "Leave this empty if you only want exercises "
        "that require no equipment."
    )

    # Muscle group selection
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
        options=muscle_options,
        placeholder="Choose muscle groups...",
    )

    # Experience level
    st.subheader("3. Experience Level")

    experience_level = st.selectbox(
        "What is your fitness experience level?",
        options=["Beginner", "Intermediate", "Advanced"],
    )

    # Exercise category
    st.subheader("4. Exercise Category")

    exercise_category = st.selectbox(
        "What type of exercises are you looking for?",
        options=[
            "Strength",
            "Stretching",
            "Cardio",
            "Olympic",
            "Plyometrics",
            "All Categories",
        ],
    )

    # Ranking method
    st.subheader("5. Recommendation Method")

    ranking_method = st.selectbox(
        "Choose a recommendation algorithm:",
        options=[
            "Hybrid",
            "Rule-Based",
            "TF-IDF",
        ],
        help=(
            "Hybrid combines muscle relevance and text similarity. "
            "Rule-Based ranks exercises by muscle matching. "
            "TF-IDF ranks exercises by text similarity."
        ),
    )

    # Workout duration
    st.subheader("6. Workout Duration")

    workout_duration = st.slider(
        "How much time do you have for your workout?",
        min_value=15,
        max_value=120,
        value=45,
        step=5,
    )

    # Number of exercises
    st.subheader("7. Number of Exercises")

    num_exercises = st.slider(
        "How many exercises would you like?",
        min_value=1,
        max_value=12,
        value=5,
        step=1,
    )

    st.divider()

    # Generate button
    submitted = st.form_submit_button(
        "Generate Workout",
        type="primary",
        use_container_width=True,
    )


# ---------------------------------
# FILTER AND RANK EXERCISES
# ---------------------------------

if submitted:

    # Validate muscle group selection
    if not selected_muscles:
        st.warning(
            "Please select at least one target muscle group."
        )

    else:

        # Step 1: Filter by equipment, muscles, and difficulty
        filtered = filter_exercises(
            exercises,
            selected_equipment,
            selected_muscles,
            experience_level,
        )

        # Step 2: Filter by exercise category
        if exercise_category != "All Categories":

            filtered = filtered[
                filtered["category"]
                == exercise_category.lower()
            ].copy()

        # Step 3: Rank exercises using the selected method
        ranked = rank_exercises(
            all_exercises=exercises,
            filtered_exercises=filtered,
            selected_muscles=selected_muscles,
            method=ranking_method,
        )

        # Step 4: Select the top-ranked exercises
        recommendations = ranked.head(num_exercises)

        # ---------------------------------
        # RESULTS HEADER
        # ---------------------------------

        st.divider()

        st.header("Your Exercise Recommendations")

        st.success(
            "Your exercise recommendations have been generated!"
        )

        # ---------------------------------
        # DISPLAY USER PREFERENCES
        # ---------------------------------

        st.subheader("Your Workout Preferences")

        col1, col2 = st.columns(2)

        with col1:

            st.write("**Available Equipment:**")

            st.write(
                ", ".join(selected_equipment)
                if selected_equipment
                else "Bodyweight Only"
            )

            st.write("**Target Muscle Groups:**")
            st.write(", ".join(selected_muscles))

            st.write("**Experience Level:**")
            st.write(experience_level)

            st.write("**Exercise Category:**")
            st.write(exercise_category)

        with col2:

            st.write("**Workout Duration:**")
            st.write(f"{workout_duration} minutes")

            st.write("**Number of Exercises Requested:**")
            st.write(num_exercises)

            st.write("**Recommendation Algorithm:**")
            st.write(ranking_method)

            st.write("**Compatible Exercises Found:**")
            st.write(len(filtered))

        st.divider()

        # ---------------------------------
        # DISPLAY RECOMMENDATIONS
        # ---------------------------------

        if recommendations.empty:

            st.warning(
                "No exercises match your preferences. "
                "Try selecting more equipment, changing your "
                "muscle groups, or choosing a different "
                "exercise category."
            )

        else:

            st.subheader(
                f"Top {len(recommendations)} Recommended Exercises"
            )

            st.caption(
                f"Exercises are ranked using the "
                f"{ranking_method} recommendation algorithm. "
                "Higher relevance scores indicate stronger matches. "
                "Workout timing, exercise variety, and substitutions "
                "will be implemented in later phases."
            )

            # Display each recommended exercise
            for index, (_, exercise) in enumerate(
                recommendations.iterrows(),
                start=1,
            ):

                with st.expander(
                    f"{index}. {exercise['name']}",
                    expanded=True,
                ):

                    # Relevance score
                    st.metric(
                        label="Relevance Score",
                        value=f"{exercise['relevance_score']:.3f}",
                    )

                    # Individual algorithm scores
                    with st.expander("View Ranking Details"):

                        st.write(
                            "**Muscle Relevance Score:**",
                            f"{exercise['muscle_score']:.3f}",
                        )

                        st.write(
                            "**TF-IDF Similarity Score:**",
                            f"{exercise['tfidf_score']:.3f}",
                        )

                        st.write(
                            "**Final Ranking Score:**",
                            f"{exercise['relevance_score']:.3f}",
                        )

                    st.divider()

                    # Exercise information
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
                        st.write(
                            exercise["difficulty"].title()
                        )

                        st.write("**Category:**")
                        st.write(
                            exercise["category"].title()
                        )

                    with col2:

                        st.write("**Primary Muscles:**")

                        primary_muscles = exercise[
                            "primary_muscle_names"
                        ]

                        st.write(
                            ", ".join(primary_muscles)
                            if primary_muscles
                            else "Not specified"
                        )

                        st.write("**Secondary Muscles:**")

                        secondary_muscles = exercise[
                            "secondary_muscle_names"
                        ]

                        st.write(
                            ", ".join(secondary_muscles)
                            if secondary_muscles
                            else "Not specified"
                        )

                    st.divider()

                    # Description
                    st.write("**Description:**")

                    st.write(
                        exercise["description"]
                        if exercise["description"]
                        else "No description available."
                    )

                    # Instructions
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

                    # Exercise tips
                    tips = exercise["tips"]

                    if isinstance(tips, list) and tips:

                        with st.expander("Exercise Tips"):

                            for tip in tips:
                                st.write(f"- {tip}")

            # ---------------------------------
            # RECOMMENDATION SUMMARY
            # ---------------------------------

            st.divider()

            st.subheader("Recommendation Summary")

            summary = recommendations[
                [
                    "name",
                    "equipment_name",
                    "difficulty",
                    "muscle_score",
                    "tfidf_score",
                    "relevance_score",
                ]
            ].copy()

            summary = summary.rename(
                columns={
                    "name": "Exercise",
                    "equipment_name": "Equipment",
                    "difficulty": "Difficulty",
                    "muscle_score": "Muscle Score",
                    "tfidf_score": "TF-IDF Score",
                    "relevance_score": "Final Score",
                }
            )

            st.dataframe(
                summary,
                use_container_width=True,
                hide_index=True,
            )

            if len(recommendations) < num_exercises:

                st.info(
                    "Fewer compatible exercises were found "
                    "than the number requested."
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
