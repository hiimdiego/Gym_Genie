
import json
from pathlib import Path

import pandas as pd


# ---------------------------------
# FILE PATHS
# ---------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "free.en.json"


# ---------------------------------
# HELPER FUNCTIONS
# ---------------------------------

def safe_text(value):
    """Convert missing values, lists, and strings into safe text."""

    if isinstance(value, list):
        return " ".join(str(item) for item in value if item is not None)

    if isinstance(value, str):
        return value

    return ""


def safe_list(value):
    """Convert missing values into empty lists."""

    if isinstance(value, list):
        return value

    return []


# ---------------------------------
# LOAD EXERCISE DATASET
# ---------------------------------

def load_exercises():
    """Load and process the RepDB exercise dataset."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at: {DATA_PATH}\n"
            "Make sure free.en.json is inside the data folder."
        )

    # Load JSON file
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    # Convert exercises into a Pandas DataFrame
    exercises = pd.DataFrame(dataset["exercises"])

    # ---------------------------------
    # REMOVE DUPLICATES
    # ---------------------------------

    exercises = exercises.drop_duplicates(subset=["id"]).copy()

    # ---------------------------------
    # EQUIPMENT MAPPING
    # ---------------------------------

    equipment_names = {
        key: value["name"]
        for key, value in dataset["equipment"].items()
    }

    # Replace missing equipment with bodyweight
    exercises["equipment_id"] = exercises["equipment"].fillna(
        "bodyweight"
    )

    # Convert equipment IDs into readable names
    exercises["equipment_name"] = (
        exercises["equipment_id"]
        .map(equipment_names)
        .fillna("Bodyweight")
    )

    # ---------------------------------
    # MUSCLE GROUP MAPPING
    # ---------------------------------

    muscle_names = {
        key: value["name"]
        for key, value in dataset["muscles"].items()
    }

    # Convert primary muscles into readable names
    exercises["primary_muscle_names"] = (
        exercises["primary_muscles"].apply(
            lambda muscles: [
                muscle_names.get(muscle, muscle)
                for muscle in safe_list(muscles)
            ]
        )
    )

    # Convert secondary muscles into readable names
    exercises["secondary_muscle_names"] = (
        exercises["secondary_muscles"].apply(
            lambda muscles: [
                muscle_names.get(muscle, muscle)
                for muscle in safe_list(muscles)
            ]
        )
    )

    # ---------------------------------
    # CLEAN TEXT FIELDS
    # ---------------------------------

    text_columns = [
        "name",
        "description",
        "difficulty",
        "category",
        "body_part",
    ]

    for column in text_columns:
        exercises[column] = exercises[column].fillna("")

    # Normalize difficulty and category
    exercises["difficulty"] = (
        exercises["difficulty"].str.lower().str.strip()
    )

    exercises["category"] = (
        exercises["category"].str.lower().str.strip()
    )

    # ---------------------------------
    # CREATE SEARCHABLE TEXT
    # ---------------------------------

    # This text will be used later for TF-IDF
    # and cosine similarity recommendations.

    exercises["search_text"] = exercises.apply(
        lambda row: " ".join([
            safe_text(row["name"]),
            safe_text(row["description"]),
            safe_text(row["primary_muscle_names"]),
            safe_text(row["secondary_muscle_names"]),
            safe_text(row["equipment_name"]),
            safe_text(row["difficulty"]),
            safe_text(row["category"]),
            safe_text(row["body_part"]),
            safe_text(row["synonyms"]),
            safe_text(row["tags"]),
            safe_text(row["goals"]),
        ]),
        axis=1,
    )

    # ---------------------------------
    # RESET INDEX
    # ---------------------------------

    exercises = exercises.reset_index(drop=True)

    return exercises


# ---------------------------------
# TEST DATASET LOADING
# ---------------------------------

if __name__ == "__main__":

    exercises = load_exercises()

    print("\n" + "=" * 50)
    print("GYMGENIE EXERCISE DATASET")
    print("=" * 50)

    # Total exercises
    print(f"\nTotal exercises loaded: {len(exercises)}")

    # Dataset columns
    print("\nAvailable columns:")
    print(exercises.columns.tolist())

    # Preview exercises
    print("\nFirst 10 exercises:")
    print(
        exercises[
            [
                "name",
                "equipment_name",
                "difficulty",
                "category",
            ]
        ].head(10).to_string(index=False)
    )

    # Difficulty distribution
    print("\nExercises by difficulty:")
    print(exercises["difficulty"].value_counts())

    # Category distribution
    print("\nExercises by category:")
    print(exercises["category"].value_counts())

    # Equipment distribution
    print("\nTop 10 equipment types:")
    print(exercises["equipment_name"].value_counts().head(10))

    # Missing values
    print("\nMissing values:")
    print(
        exercises[
            [
                "name",
                "description",
                "difficulty",
                "category",
            ]
        ].isnull().sum()
    )

    # Example searchable text
    print("\nExample searchable text:")
    print(exercises.iloc[0]["search_text"])

    print("\nDataset loaded successfully!")
