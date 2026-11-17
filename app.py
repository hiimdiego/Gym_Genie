
import streamlit as st

# ---------------------------------
# PAGE CONFIGURATION
# ---------------------------------

st.set_page_config(
    page_title="GymGenie",
    page_icon="💪",
    layout="wide"
)

# ---------------------------------
# HEADER
# ---------------------------------

st.title("💪 GymGenie")
st.subheader("Your Personalized Workout Planner")

st.write(
    "Build a workout tailored to your available equipment, "
    "target muscle groups, experience level, and schedule."
)

st.divider()

# ---------------------------------
# WORKOUT PREFERENCES
# ---------------------------------

st.header("Customize Your Workout")

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
    "Treadmill"
]

selected_equipment = st.multiselect(
    "Select the equipment you currently have access to:",
    options=equipment_options,
    placeholder="Choose available equipment..."
)

st.caption(
    "Leave this empty if you want a bodyweight-only workout."
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
    "Core"
]

selected_muscles = st.multiselect(
    "Which muscle groups would you like to target?",
    options=muscle_options,
    placeholder="Choose muscle groups..."
)

# Experience level
st.subheader("3. Experience Level")

experience_level = st.selectbox(
    "What is your fitness experience level?",
    options=["Beginner", "Intermediate", "Advanced"]
)

# Workout duration
st.subheader("4. Workout Duration")

workout_duration = st.slider(
    "How much time do you have for your workout?",
    min_value=15,
    max_value=120,
    value=45,
    step=5,
    format="%d minutes"
)

# Number of exercises
st.subheader("5. Number of Exercises")

num_exercises = st.slider(
    "How many exercises would you like?",
    min_value=1,
    max_value=12,
    value=5,
    step=1
)

st.divider()

# ---------------------------------
# GENERATE WORKOUT
# ---------------------------------

st.header("Generate Your Workout")

if st.button("Generate Workout", type="primary"):

    # Validate user input
    if not selected_muscles:
        st.warning(
            "Please select at least one target muscle group."
        )

    else:
        st.success("Your workout preferences have been submitted!")

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

        with col2:
            st.write("**Workout Duration:**")
            st.write(f"{workout_duration} minutes")

            st.write("**Number of Exercises:**")
            st.write(num_exercises)

        st.divider()

        st.info(
            "Workout recommendations will appear here "
            "once the recommendation engine is implemented."
        )

# ---------------------------------
# FOOTER
# ---------------------------------

st.divider()

st.caption(
    "GymGenie | CS 410: Text Information Systems"
)
