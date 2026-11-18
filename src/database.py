
import json
import sqlite3
from pathlib import Path


# ---------------------------------
# DATABASE CONFIGURATION
# ---------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "gymgenie.db"


def get_connection():
    """Connect to the local GymGenie database."""

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


# ---------------------------------
# CREATE DATABASE
# ---------------------------------

def initialize_database():
    """Create the saved workouts table if needed."""

    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS saved_workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                preferences TEXT NOT NULL,
                exercises TEXT NOT NULL
            )
        """)


# ---------------------------------
# SAVE WORKOUT
# ---------------------------------

def save_workout(name, preferences, workout):
    """
    Save a workout and its preferences.

    Store exercise IDs and workout prescriptions,
    not full RepDB exercise records.
    """

    if not name.strip():
        raise ValueError("Workout name cannot be empty.")

    if workout.empty:
        raise ValueError("Cannot save an empty workout.")

    exercise_records = []

    for _, exercise in workout.iterrows():
        exercise_records.append({
            "id": str(exercise["id"]),
            "sets": int(exercise["sets"]),
            "reps": str(exercise["reps"]),
            "rest_seconds": int(
                exercise["rest_seconds"]
            ),
            "prescription_type": str(
                exercise["prescription_type"]
            ),
            "estimated_minutes": float(
                exercise["estimated_minutes"]
            ),
        })

    initialize_database()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO saved_workouts
                (name, preferences, exercises)
            VALUES (?, ?, ?)
            """,
            (
                name.strip(),
                json.dumps(preferences),
                json.dumps(exercise_records),
            ),
        )

        return cursor.lastrowid


# ---------------------------------
# LIST SAVED WORKOUTS
# ---------------------------------

def get_saved_workouts():
    """Return saved workouts, newest first."""

    initialize_database()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, created_at
            FROM saved_workouts
            ORDER BY id DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


# ---------------------------------
# LOAD SAVED WORKOUT
# ---------------------------------

def load_saved_workout(workout_id):
    """Load one saved workout by its database ID."""

    initialize_database()

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM saved_workouts
            WHERE id = ?
            """,
            (workout_id,),
        ).fetchone()

    if row is None:
        return None

    result = dict(row)

    result["preferences"] = json.loads(
        result["preferences"]
    )

    result["exercises"] = json.loads(
        result["exercises"]
    )

    return result


# ---------------------------------
# DELETE SAVED WORKOUT
# ---------------------------------

def delete_saved_workout(workout_id):
    """Delete one saved workout."""

    initialize_database()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM saved_workouts
            WHERE id = ?
            """,
            (workout_id,),
        )

        return cursor.rowcount > 0


# ---------------------------------
# TEST DATABASE
# ---------------------------------

if __name__ == "__main__":

    initialize_database()

    print("\nGymGenie database initialized.")
    print(f"Database location: {DATABASE_PATH}")

    saved = get_saved_workouts()

    print(f"Saved workouts found: {len(saved)}")

    for workout in saved:
        print(
            f"{workout['id']}: {workout['name']} "
            f"({workout['created_at']})"
        )

    print("\nDatabase test completed successfully!")
