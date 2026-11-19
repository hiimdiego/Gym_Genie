
import html
import pandas as pd
import streamlit as st

from src.data_loader import load_exercises
from src.exercise_filter import filter_exercises, filter_by_equipment
from src.ranking import rank_exercises
from src.substitutions import get_substitutions
from src.workout import (
    generate_workout,
    get_prescription,
    estimate_exercise_seconds,
    WARMUP_MINUTES,
)
from src.database import (
    initialize_database,
    save_workout,
    get_saved_workouts,
    load_saved_workout,
    delete_saved_workout,
)


# ---------------------------------
# PAGE CONFIGURATION
# ---------------------------------

st.set_page_config(
    page_title="GymGenie | Workout Planner",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------
# CUSTOM STYLING
# ---------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --paper: #FAFAF8;
    --ink: #1D2521;
    --muted: #6B756E;
    --line: #E3E8E2;
    --accent: #385A47;
    --button-red: #C63D36;
    --button-red-hover: #AB302A;
}

/* Main application */

html, body, [class*="css"], [data-testid="stApp"] {
    font-family: 'DM Sans', sans-serif;
}

[data-testid="stAppViewContainer"] {
    background-color: var(--paper);
    color: var(--ink);
}

[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1160px;
    padding-top: 2.8rem;
    padding-bottom: 4rem;
}

/* Sidebar */

[data-testid="stSidebar"] {
    background-color: #F2F4F0 !important;
    border-right: 1px solid var(--line);
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 2rem;
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span {
    color: var(--ink);
}

.app-brand {
    font-family: 'Manrope', sans-serif;
    font-size: 1.4rem;
    font-weight: 800;
    letter-spacing: -.06em;
    color: #1D2521 !important;
    margin-bottom: .25rem;
}

.app-tag {
    color: var(--muted) !important;
    font-size: .83rem;
    margin-bottom: 1.7rem;
}

/* Typography */

h1, h2, h3 {
    font-family: 'Manrope', sans-serif;
    letter-spacing: -.045em;
    color: var(--ink) !important;
}

h1 {
    font-size: clamp(2.5rem, 4.8vw, 4.4rem) !important;
    font-weight: 800 !important;
    line-height: 1.1 !important;
}

h2 {
    font-size: 1.65rem !important;
    font-weight: 750 !important;
}

h3 {
    font-size: 1.14rem !important;
    font-weight: 700 !important;
}

p, li, label {
    color: var(--ink);
}

[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p {
    color: var(--muted) !important;
}

/* Dividers */

hr {
    border-color: var(--line) !important;
    margin: 1.8rem 0 !important;
}

/* Forms */

[data-testid="stForm"] {
    border: 1px solid var(--line);
    background-color: #FFFFFF;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
}

/* All primary buttons: red background, white text */

.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] button[kind="primary"] {
    background-color: var(--button-red) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--button-red) !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    min-height: 2.85rem;
}

.stButton > button[kind="primary"] *,
[data-testid="stFormSubmitButton"] button[kind="primary"] * {
    color: #FFFFFF !important;
}

.stButton > button[kind="primary"]:hover,
[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
    background-color: var(--button-red-hover) !important;
    border-color: var(--button-red-hover) !important;
    color: #FFFFFF !important;
}

.stButton > button[kind="primary"]:hover *,
[data-testid="stFormSubmitButton"] button[kind="primary"]:hover * {
    color: #FFFFFF !important;
}

.stButton > button[kind="primary"]:focus,
[data-testid="stFormSubmitButton"] button[kind="primary"]:focus {
    color: #FFFFFF !important;
}

.stButton > button[kind="primary"]:focus *,
[data-testid="stFormSubmitButton"] button[kind="primary"]:focus * {
    color: #FFFFFF !important;
}

/* Secondary buttons */

.stButton > button,
[data-testid="stFormSubmitButton"] button {
    border-radius: 8px !important;
    font-weight: 650 !important;
}

.stButton > button[kind="secondary"] {
    background-color: #FFFFFF !important;
    color: var(--ink) !important;
    border: 1px solid var(--line) !important;
}

.stButton > button[kind="secondary"] * {
    color: var(--ink) !important;
}

.stButton > button[kind="secondary"]:hover {
    border-color: var(--accent) !important;
    background-color: #F2F4F0 !important;
}

/* Metric cards */

[data-testid="stMetric"] {
    padding: 1rem 1.2rem;
    background-color: #FFFFFF !important;
    border: 1px solid var(--line);
    border-radius: 12px;
    color: #1D2521 !important;
}

[data-testid="stMetric"] * {
    color: #1D2521 !important;
}

[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] *,
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] * {
    color: #1D2521 !important;
}

[data-testid="stMetricValue"] {
    font-family: 'Manrope', sans-serif;
    letter-spacing: -.055em;
}

/* Input fields */

[data-baseweb="input"] > div {
    background-color: #FFFFFF !important;
    border-radius: 8px !important;
}

[data-baseweb="input"] input {
    color: #1D2521 !important;
    background-color: #FFFFFF !important;
}

[data-baseweb="input"] input::placeholder {
    color: #7C857F !important;
}

/* Dropdowns and multiselect fields */

[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: #1D2521 !important;
    border-radius: 8px !important;
}

[data-baseweb="select"] input,
[data-baseweb="select"] span {
    color: #1D2521 !important;
}

[data-baseweb="select"] svg {
    fill: #1D2521 !important;
    color: #1D2521 !important;
}

/* Open dropdown menus */

[data-baseweb="popover"],
[data-baseweb="menu"],
[data-baseweb="menu"] ul,
[data-baseweb="menu"] li {
    background-color: #FFFFFF !important;
    color: #1D2521 !important;
}

[data-baseweb="popover"] *,
[data-baseweb="menu"] * {
    color: #1D2521 !important;
}

/* Dropdown option states */

[role="option"] {
    background-color: #FFFFFF !important;
    color: #1D2521 !important;
}

[role="option"]:hover,
[role="option"][aria-selected="true"] {
    background-color: #E9EFEA !important;
    color: #1D2521 !important;
}

[role="option"][data-highlighted="true"] {
    background-color: #E9EFEA !important;
    color: #1D2521 !important;
}

/* Multiselect selected tags */

[data-baseweb="tag"] {
    background-color: #E9EFEA !important;
}

[data-baseweb="tag"] * {
    color: #1D2521 !important;
}

/* Expandable exercise sections */

[data-testid="stExpander"] {
    border: 1px solid var(--line);
    background-color: #FFFFFF;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: .55rem;
}

[data-testid="stExpander"] details summary {
    padding: .5rem .35rem;
}

[data-testid="stExpander"] details summary p {
    font-weight: 650;
}

/* Data tables */

[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
}

/* Custom text styles */

.hero-kicker {
    color: var(--accent);
    text-transform: uppercase;
    font-weight: 800;
    letter-spacing: .16em;
    font-size: .73rem;
    margin-bottom: 1.1rem;
}

.hero-copy {
    max-width: 640px;
    color: var(--muted);
    font-size: 1.06rem;
    line-height: 1.7;
    margin-top: .65rem;
    margin-bottom: 2rem;
}

.section-kicker {
    color: var(--accent);
    text-transform: uppercase;
    font-size: .69rem;
    letter-spacing: .15em;
    font-weight: 800;
    margin-bottom: .35rem;
}

.section-copy {
    font-size: .91rem;
    color: var(--muted);
    margin-top: -.4rem;
    margin-bottom: 1rem;
}

.detail-label {
    color: var(--muted);
    font-size: .72rem;
    text-transform: uppercase;
    font-weight: 800;
    letter-spacing: .08em;
    margin-bottom: .15rem;
}

.detail-value {
    color: var(--ink);
    font-size: .94rem;
    margin-bottom: .7rem;
}

.footer-text {
    color: var(--muted);
    font-size: .8rem;
}

.footer-text a {
    color: var(--accent);
}


/* =========================================
   1. FIX WORKOUT EXERCISE DROPDOWNS
   ========================================= */

/* Keep exercise panels white when opened */
[data-testid="stExpander"],
[data-testid="stExpander"] details,
[data-testid="stExpander"] details[open],
[data-testid="stExpander"] summary {
    background-color: #FFFFFF !important;
    color: #1D2521 !important;
}

/* Keep dropdown headers readable */
[data-testid="stExpander"] summary *,
[data-testid="stExpander"] details[open] summary *,
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    color: #1D2521 !important;
}

/* Light background when hovering or clicking */
[data-testid="stExpander"] summary:hover,
[data-testid="stExpander"] summary:focus,
[data-testid="stExpander"] summary:active {
    background-color: #F2F4F0 !important;
    color: #1D2521 !important;
}

/* Fix text inside opened exercise details */
[data-testid="stExpanderDetails"] p,
[data-testid="stExpanderDetails"] span,
[data-testid="stExpanderDetails"] li,
[data-testid="stExpanderDetails"] strong {
    color: #1D2521 !important;
}

/* Fix dropdown arrows */
[data-testid="stExpander"] summary svg {
    color: #1D2521 !important;
    stroke: #1D2521 !important;
}


/* =========================================
   2. MAKE ALL PRIMARY BUTTONS MATCH
   ========================================= */

/* Open Workout, Save Workout, Generate My Workout */
.stButton button[kind="primary"],
[data-testid="stFormSubmitButton"] button,
button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-formSubmit"] {
    background-color: #C63D36 !important;
    border: 1px solid #C63D36 !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
}

/* Force button text to stay white */
.stButton button[kind="primary"] *,
[data-testid="stFormSubmitButton"] button *,
button[data-testid="stBaseButton-primary"] *,
button[data-testid="stBaseButton-formSubmit"] * {
    color: #FFFFFF !important;
}

/* Darker red when hovering */
.stButton button[kind="primary"]:hover,
[data-testid="stFormSubmitButton"] button:hover,
button[data-testid="stBaseButton-primary"]:hover,
button[data-testid="stBaseButton-formSubmit"]:hover {
    background-color: #AB302A !important;
    border-color: #AB302A !important;
    color: #FFFFFF !important;
}

/* Keep text white when clicked or focused */
.stButton button[kind="primary"]:focus *,
.stButton button[kind="primary"]:active *,
[data-testid="stFormSubmitButton"] button:focus *,
[data-testid="stFormSubmitButton"] button:active * {
    color: #FFFFFF !important;
}


/* =========================================
   3. ALWAYS SHOW SIDEBAR CLOSE BUTTON
   ========================================= */

/* Prevent sidebar controls from fading out */
[data-testid="stSidebarHeader"],
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapseButton"] button {
    opacity: 1 !important;
    visibility: visible !important;
}

/* Keep close icon visible */
[data-testid="stSidebarCollapseButton"] svg {
    color: #1D2521 !important;
    stroke: #1D2521 !important;
    opacity: 1 !important;
}

/* Sidebar close button hover */
[data-testid="stSidebarCollapseButton"] button:hover {
    background-color: #E3E8E2 !important;
}



/* =========================================
   4. FIX SIDEBAR OPEN BUTTON
   ========================================= */

/* Keep sidebar open button visible */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stExpandSidebarButton"] {
    opacity: 1 !important;
    visibility: visible !important;
}

/* Button background and text color */
[data-testid="collapsedControl"] button,
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="stExpandSidebarButton"] button,
button[kind="headerNoPadding"] {
    background-color: #E3E8E2 !important;
    color: #1D2521 !important;
    border-radius: 8px !important;
}

/* Make sidebar open icon dark */
[data-testid="collapsedControl"] svg,
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="stExpandSidebarButton"] svg,
button[kind="headerNoPadding"] svg {
    color: #1D2521 !important;
    stroke: #1D2521 !important;
    fill: #1D2521 !important;
}

/* Fix icons that use SVG paths */
[data-testid="collapsedControl"] svg path,
[data-testid="stSidebarCollapsedControl"] svg path,
[data-testid="stExpandSidebarButton"] svg path,
button[kind="headerNoPadding"] svg path {
    fill: #1D2521 !important;
    stroke: #1D2521 !important;
}

/* Darker background when hovering */
[data-testid="collapsedControl"] button:hover,
[data-testid="stSidebarCollapsedControl"] button:hover,
[data-testid="stExpandSidebarButton"] button:hover,
button[kind="headerNoPadding"]:hover {
    background-color: #D3DBD3 !important;
}


/* Match sidebar open icon to sidebar text */
[data-testid="stExpandSidebarButton"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    color: #1D2521 !important;
}

/* Force icon and its contents to black */
[data-testid="stExpandSidebarButton"] *,
[data-testid="collapsedControl"] *,
[data-testid="stSidebarCollapsedControl"] * {
    color: #1D2521 !important;
    fill: #1D2521 !important;
}

/* Support Streamlit's Material icon font */
[data-testid="stExpandSidebarButton"] span,
[data-testid="collapsedControl"] span,
[data-testid="stSidebarCollapsedControl"] span {
    color: #1D2521 !important;
    -webkit-text-fill-color: #1D2521 !important;
}


/* =========================================
   5. STYLE THE MENU BUTTON NEXT TO DEPLOY
   ========================================= */

[data-testid="stMainMenu"],
[data-testid="stMainMenu"] button,
[data-testid="stToolbar"] [data-testid="stMainMenu"],
[data-testid="stToolbar"] [data-testid="stMainMenu"] button {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border-radius: 8px !important;
    box-shadow: none !important;
}

/* Replace Streamlit's menu glyph with a gear */
[data-testid="stMainMenu"] button svg {
    display: none !important;
}

[data-testid="stMainMenu"] button::before {
    content: "⚙︎";
    color: #1D2521 !important;
    font-family: Arial, sans-serif;
    font-size: 1.25rem;
    line-height: 1;
}

[data-testid="stMainMenu"] button:hover {
    background-color: #E3E8E2 !important;
}

</style>
""", unsafe_allow_html=True)


# ---------------------------------
# LOAD DATA
# ---------------------------------

@st.cache_data
def get_exercises():
    return load_exercises()


try:
    exercises = get_exercises()
    initialize_database()

except (FileNotFoundError, KeyError, ValueError) as error:
    st.error(f"Unable to initialize GymGenie: {error}")
    st.stop()


# ---------------------------------
# INPUT OPTIONS
# ---------------------------------

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

CATEGORIES = [
    "Strength",
    "Stretching",
    "Cardio",
    "Olympic",
    "Plyometrics",
    "All Categories",
]

RANKING_METHODS = [
    "Hybrid",
    "Rule-Based",
    "TF-IDF",
]


# ---------------------------------
# SESSION STATE
# ---------------------------------

defaults = {
    "workout": None,
    "workout_preferences": None,
    "ranked_results": None,
    "replacement_equipment": [],
    "workout_name": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------------------------
# HELPER FUNCTIONS
# ---------------------------------

def safe(value):
    return html.escape(str(value))


def list_as_text(value):
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "Not specified"

    if value is None:
        return "Not specified"

    return str(value) or "Not specified"


def calculate_workout_time(workout, preferences):
    """Calculate estimated workout duration."""

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


def restore_workout(saved):
    """Reconstruct a saved workout using exercise IDs."""

    preferences = saved["preferences"]

    exercise_lookup = exercises.set_index("id")

    records = []

    for saved_exercise in saved["exercises"]:

        exercise_id = saved_exercise["id"]

        if exercise_id not in exercise_lookup.index:
            st.warning(
                f"Exercise {exercise_id} was not found "
                "in the current dataset."
            )
            continue

        record = exercise_lookup.loc[
            exercise_id
        ].to_dict()

        record["id"] = exercise_id

        for field in [
            "sets",
            "reps",
            "rest_seconds",
            "prescription_type",
            "estimated_minutes",
        ]:
            record[field] = saved_exercise[field]

        records.append(record)

    if not records:
        return pd.DataFrame(), pd.DataFrame()

    workout = pd.DataFrame(records)

    ranked = rank_exercises(
        all_exercises=exercises,
        filtered_exercises=workout,
        selected_muscles=preferences["muscles"],
        method=preferences["ranking"],
    )

    score_lookup = ranked.set_index("id")

    for column in [
        "muscle_score",
        "tfidf_score",
        "relevance_score",
    ]:
        workout[column] = workout["id"].map(
            score_lookup[column]
        ).fillna(0.0)

    return workout, ranked


def section_header(kicker, heading, subtitle=None):

    st.markdown(
        f'<div class="section-kicker">{safe(kicker)}</div>',
        unsafe_allow_html=True,
    )

    st.subheader(heading)

    if subtitle:
        st.markdown(
            f'<div class="section-copy">{safe(subtitle)}</div>',
            unsafe_allow_html=True,
        )


def detail(label, value):

    st.markdown(
        f'<div class="detail-label">{safe(label)}</div>'
        f'<div class="detail-value">{safe(value)}</div>',
        unsafe_allow_html=True,
    )


def display_exercise(exercise, number, workout_mode=False):
    """Display exercise details."""

    with st.expander(
        f"{number:02d}   {exercise['name']}",
        expanded=(number == 1),
    ):

        if workout_mode:

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.metric(
                    "Sets",
                    int(exercise["sets"]),
                )

            with c2:
                label = (
                    "Hold"
                    if exercise["prescription_type"] == "hold"
                    else "Reps"
                )

                st.metric(
                    label,
                    exercise["reps"],
                )

            with c3:
                st.metric(
                    "Rest",
                    f"{int(exercise['rest_seconds'])}s",
                )

            with c4:
                st.metric(
                    "Est. time",
                    f"{float(exercise['estimated_minutes']):.1f}m",
                )

        st.write("")

        left, right = st.columns(2, gap="large")

        with left:

            detail(
                "Equipment",
                exercise.get(
                    "equipment_name",
                    "Not specified",
                ),
            )

            extra = exercise.get(
                "additional_required_equipment"
            )

            if isinstance(extra, list) and extra:
                detail(
                    "Additional equipment IDs",
                    list_as_text(extra),
                )

            detail(
                "Level",
                str(
                    exercise.get(
                        "difficulty",
                        "Not specified",
                    )
                ).title(),
            )

            detail(
                "Category",
                str(
                    exercise.get(
                        "category",
                        "Not specified",
                    )
                ).title(),
            )

        with right:

            detail(
                "Primary muscles",
                list_as_text(
                    exercise.get("primary_muscle_names")
                ),
            )

            detail(
                "Secondary muscles",
                list_as_text(
                    exercise.get("secondary_muscle_names")
                ),
            )

            if "relevance_score" in exercise.index:
                detail(
                    "Relevance score",
                    f"{float(exercise['relevance_score']):.3f}",
                )

        st.markdown("**About this exercise**")

        st.write(
            exercise.get("description")
            or "No description available."
        )

        instructions = exercise.get("instructions")

        if isinstance(instructions, list) and instructions:

            st.markdown("**How to do it**")

            for idx, instruction in enumerate(
                instructions,
                start=1,
            ):
                st.write(f"{idx}. {instruction}")

        tips = exercise.get("tips")

        if isinstance(tips, list) and tips:

            with st.expander("Tips"):
                for tip in tips:
                    st.write(f"• {tip}")

        if (
            "muscle_score" in exercise.index
            and "tfidf_score" in exercise.index
        ):

            with st.expander(
                "Why this exercise was recommended"
            ):

                st.write(
                    "Muscle score:",
                    f"{float(exercise['muscle_score']):.3f}",
                )

                st.write(
                    "TF-IDF score:",
                    f"{float(exercise['tfidf_score']):.3f}",
                )


# ---------------------------------
# SIDEBAR
# ---------------------------------

with st.sidebar:

    st.markdown(
        """
        <div class="app-brand">
            GymGenie<span style="color:#63816c">.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="app-tag">Your workout library</div>',
        unsafe_allow_html=True,
    )

    st.markdown("**Saved workouts**")

    saved_workouts = get_saved_workouts()

    if not saved_workouts:

        st.caption(
            "Nothing saved yet. Generate a strength "
            "workout and save it here."
        )

    else:

        saved_by_id = {
            item["id"]: item
            for item in saved_workouts
        }

        selected_saved_id = st.selectbox(
            "Choose workout",
            options=list(saved_by_id.keys()),
            format_func=lambda workout_id: (
                saved_by_id[workout_id]["name"]
                + " · "
                + saved_by_id[workout_id]["created_at"]
            ),
        )

        if st.button(
            "Open workout",
            type="primary",
            use_container_width=True,
        ):

            saved = load_saved_workout(
                selected_saved_id
            )

            if saved is not None:

                restored, ranked = restore_workout(saved)

                st.session_state.workout = restored
                st.session_state.ranked_results = ranked

                st.session_state.workout_preferences = (
                    saved["preferences"]
                )

                st.session_state.replacement_equipment = (
                    saved["preferences"]["equipment"].copy()
                )

                st.session_state.workout_name = saved["name"]

                st.rerun()

        with st.expander("Manage saved workout"):

            confirm_delete = st.checkbox(
                "I want to delete this workout"
            )

            if st.button(
                "Delete workout",
                disabled=not confirm_delete,
                use_container_width=True,
            ):

                delete_saved_workout(
                    selected_saved_id
                )

                st.success("Workout deleted.")

                st.rerun()

    with st.expander("Recommendation & score guide"):
        st.markdown(
            """
            **Recommendation methods**

            - **Hybrid:** Combines muscle relevance (75%) and text similarity (25%).
            - **Rule-Based:** Ranks by muscle relevance only.
            - **TF-IDF:** Ranks by text similarity only.

            **Scores**

            - **Muscle score (0–1):** For each selected muscle group, a primary
              muscle match earns 1.0, a secondary match earns 0.35, and no
              match earns 0. The score is averaged across your selected groups.
            - **TF-IDF score (0–1):** Cosine similarity between your selected
              muscle terms and the exercise's searchable metadata: name,
              description, muscles, equipment, difficulty, category, body
              part, tags, goals, and synonyms. Higher means closer text match.

            Equipment and experience filters are applied before ranking.
            Scores indicate relative match, not exercise quality.
            """
        )

    st.divider()

    st.caption(
        "CS 410 · Text Information Systems"
    )


# ---------------------------------
# HEADER
# ---------------------------------

st.markdown(
    '<div class="hero-kicker">TRAIN ON YOUR TERMS</div>',
    unsafe_allow_html=True,
)

st.title("A workout that fits\nwhat you have.")

st.markdown(
    """
    <div class="hero-copy">
        Choose your equipment, focus areas, and available time.
        GymGenie finds exercises that fit, then builds a workout
        you can actually do.
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------
# WORKOUT PREFERENCES
# ---------------------------------

section_header(
    "01 / Build",
    "Plan your session",
    "Set your preferences. You can change equipment "
    "later if you need substitutions.",
)

with st.form(
    "workout_form",
    clear_on_submit=False,
):

    c1, c2 = st.columns(
        2,
        gap="large",
    )

    with c1:

        selected_equipment = st.multiselect(
            "Available equipment",
            EQUIPMENT_OPTIONS,
            help=(
                "Leave empty for exercises "
                "that need no equipment."
            ),
        )

        selected_muscles = st.multiselect(
            "Target muscle groups",
            MUSCLE_OPTIONS,
        )

        experience_level = st.selectbox(
            "Experience level",
            [
                "Beginner",
                "Intermediate",
                "Advanced",
            ],
        )

        exercise_category = st.selectbox(
            "Exercise type",
            CATEGORIES,
        )

    with c2:

        workout_duration = st.slider(
            "Time available (minutes)",
            min_value=15,
            max_value=120,
            value=45,
            step=5,
        )

        num_exercises = st.slider(
            "Number of exercises",
            min_value=1,
            max_value=12,
            value=5,
        )

        ranking_method = st.selectbox(
            "Recommendation method",
            RANKING_METHODS,
            help=(
                "Hybrid combines text similarity "
                "and muscle relevance. Switch methods "
                "to compare rankings for CS 410."
            ),
        )

        st.caption(
            "No equipment selected = "
            "bodyweight-compatible exercises."
        )

    submitted = st.form_submit_button(
        "Generate my workout",
        type="primary",
        use_container_width=True,
    )


# ---------------------------------
# GENERATE WORKOUT
# ---------------------------------

if submitted:

    if not selected_muscles:

        st.warning(
            "Choose at least one muscle group to continue."
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

        st.session_state.workout_name = ""

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
# DISPLAY RESULTS
# ---------------------------------

preferences = st.session_state.workout_preferences

if preferences is not None:

    st.divider()

    section_header(
        "02 / Results",
        "Your session",
    )

    st.caption(
        f"{', '.join(preferences['muscles'])} · "
        f"{preferences['experience']} · "
        f"{preferences['ranking']} ranking · "
        f"{', '.join(preferences['equipment']) or 'Bodyweight'}"
    )

    ranked = st.session_state.ranked_results

    st.caption(
        f"{len(ranked)} compatible exercises found"
    )

    if ranked.empty:

        st.warning(
            "No compatible exercises found. "
            "Try changing your equipment or muscle selections."
        )

    # ---------------------------------
    # STRENGTH WORKOUT RESULTS
    # ---------------------------------

    elif preferences["category"] == "Strength":

        workout = st.session_state.workout

        if workout is None or workout.empty:

            st.warning(
                "No workout fits these preferences. "
                "Try allowing more time or selecting fewer exercises."
            )

        else:

            total_time = calculate_workout_time(
                workout,
                preferences,
            )

            c1, c2, c3 = st.columns(3)

            with c1:
                st.metric(
                    "Exercises",
                    len(workout),
                )

            with c2:
                st.metric(
                    "Estimated time",
                    f"{total_time:.1f} min",
                )

            with c3:
                st.metric(
                    "Your time limit",
                    f"{preferences['duration']} min",
                )

            st.caption(
                f"Time estimate includes a "
                f"{WARMUP_MINUTES}-minute warm-up."
            )

            if len(workout) < preferences["count"]:

                st.info(
                    "Fewer exercises were selected to stay "
                    "within your time, equipment, and variety constraints."
                )

            # ---------------------------------
            # EXERCISE SUBSTITUTIONS
            # ---------------------------------

            st.write("")

            section_header(
                "03 / Adjust",
                "Change your setup",
                "Lost access to a machine? Update your "
                "equipment to find suitable replacements.",
            )

            replacement_equipment = st.multiselect(
                "Equipment available now",
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
                    f"{len(incompatible_ids)} exercise(s) need "
                    "equipment you don't currently have."
                )

            else:

                st.success(
                    "Every exercise works with your current equipment."
                )

            # ---------------------------------
            # EXERCISE LIST
            # ---------------------------------

            st.write("")

            section_header(
                "04 / Exercises",
                "Your workout",
                "Open an exercise to see details, "
                "tips, and ranking scores.",
            )

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
                        f"{exercise['name']} needs unavailable "
                        "equipment. Choose a replacement below."
                    )

                with st.expander(
                    f"Swap exercise {index:02d} · {exercise['name']}"
                ):

                    excluded_ids = [
                        item_id
                        for item_id in workout["id"].tolist()
                        if item_id != exercise_id
                    ]

                    alternatives = get_substitutions(
                        original_exercise=exercise,
                        all_exercises=exercises,
                        available_equipment=replacement_equipment,
                        experience_level=preferences["experience"],
                        excluded_ids=excluded_ids,
                        max_results=5,
                    )

                    if alternatives.empty:

                        st.info(
                            "No compatible alternatives found "
                            "for this equipment selection."
                        )

                    else:

                        alternatives_by_id = {
                            row["id"]: row
                            for _, row in alternatives.iterrows()
                        }

                        selected_id = st.selectbox(
                            "Replacement exercise",
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

                        col_a, col_b = st.columns(2)

                        with col_a:
                            detail(
                                "Equipment",
                                replacement["equipment_name"],
                            )

                        with col_b:
                            detail(
                                "Primary muscles",
                                list_as_text(
                                    replacement["primary_muscle_names"]
                                ),
                            )

                        st.caption(
                            f"Substitution score: "
                            f"{float(replacement['substitution_score']):.3f}"
                        )

                        if st.button(
                            "Use this exercise",
                            key=f"replace_{exercise_id}",
                            type="primary",
                        ):

                            prescription = get_prescription(
                                replacement,
                                preferences["experience"],
                                preferences["duration"],
                            )

                            new_row = replacement.to_dict()

                            for field in [
                                "sets",
                                "reps",
                                "rest_seconds",
                                "prescription_type",
                            ]:
                                new_row[field] = prescription[field]

                            new_row["estimated_minutes"] = round(
                                estimate_exercise_seconds(
                                    prescription
                                ) / 60,
                                1,
                            )

                            replacement_ranked = rank_exercises(
                                all_exercises=exercises,
                                filtered_exercises=alternatives[
                                    alternatives["id"] == selected_id
                                ],
                                selected_muscles=preferences["muscles"],
                                method=preferences["ranking"],
                            )

                            for score_column in [
                                "muscle_score",
                                "tfidf_score",
                                "relevance_score",
                            ]:
                                new_row[score_column] = float(
                                    replacement_ranked.iloc[0][
                                        score_column
                                    ]
                                )

                            records = workout.to_dict("records")

                            records[index - 1] = new_row

                            updated = pd.DataFrame(records)

                            new_duration = calculate_workout_time(
                                updated,
                                preferences,
                            )

                            if new_duration > preferences["duration"]:

                                st.error(
                                    "That replacement would exceed "
                                    "your workout time limit."
                                )

                            else:

                                st.session_state.workout = updated

                                st.rerun()

            # ---------------------------------
            # SAVE WORKOUT
            # ---------------------------------

            st.write("")

            section_header(
                "05 / Keep",
                "Save this workout",
                "Store the current version so "
                "you can use it again.",
            )

            if "save_message" in st.session_state:

                st.success(
                    st.session_state.pop("save_message")
                )

            name_col, button_col = st.columns(
                [3, 1],
                vertical_alignment="bottom",
            )

            with name_col:

                workout_name = st.text_input(
                    "Workout name",
                    placeholder="e.g. Upper body · Hotel gym",
                    key="workout_name",
                )

            with button_col:

                save_clicked = st.button(
                    "Save workout",
                    type="primary",
                    use_container_width=True,
                )

            if save_clicked:

                if not workout_name.strip():

                    st.warning(
                        "Enter a name before saving your workout."
                    )

                else:

                    saved_id = save_workout(
                        workout_name,
                        preferences,
                        workout,
                    )

                    st.session_state["save_message"] = (
                        f"Workout saved. ID: {saved_id}"
                    )

                    st.rerun()

            # ---------------------------------
            # WORKOUT SUMMARY
            # ---------------------------------

            with st.expander(
                "View workout summary table"
            ):

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
                    "Est. time (min)",
                ]

                st.dataframe(
                    summary,
                    use_container_width=True,
                    hide_index=True,
                )

                st.caption(
                    "To keep substitutions, save the modified "
                    "workout. Saving creates a new entry."
                )

    # ---------------------------------
    # OTHER EXERCISE CATEGORIES
    # ---------------------------------

    else:

        section_header(
            "03 / Explore",
            "Ranked exercise matches",
        )

        st.caption(
            "Full workout generation and saved workouts "
            "are currently supported for Strength only."
        )

        for index, (_, exercise) in enumerate(
            ranked.head(
                preferences["count"]
            ).iterrows(),
            start=1,
        ):

            display_exercise(
                exercise,
                index,
            )


# ---------------------------------
# FOOTER
# ---------------------------------

st.divider()

st.markdown(
    """
    <div class="footer-text">
        GymGenie · CS 410: Text Information Systems ·
        <a href="https://repdb.co" target="_blank">
            Exercise data: RepDB
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)
