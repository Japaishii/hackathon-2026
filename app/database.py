"""SQLite persistence for animals and immutable assessment snapshots."""
import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DB_PATH = Path(os.environ.get("LEITECHECK_DB", Path(__file__).resolve().parents[1] / "data" / "leitecheck.sqlite3"))


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize() -> None:
    with closing(connect()) as conn, conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS animals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identifier TEXT NOT NULL UNIQUE,
            breed TEXT,
            age_months INTEGER,
            days_in_milk INTEGER,
            notes TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_id INTEGER REFERENCES animals(id) ON DELETE SET NULL,
            created_at TEXT NOT NULL,
            answers_json TEXT NOT NULL,
            result_json TEXT NOT NULL,
            follow_up TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_assessments_animal ON assessments(animal_id, created_at DESC);
        """)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(animals)")}
        for name in ("productive_state", "transition_stage"):
            if name not in columns:
                conn.execute(f"ALTER TABLE animals ADD COLUMN {name} TEXT")


def create_animal(data: dict[str, Any]) -> dict[str, Any]:
    created = datetime.now(timezone.utc).isoformat()
    with closing(connect()) as conn, conn:
        cur = conn.execute("INSERT INTO animals(identifier,breed,age_months,days_in_milk,notes,created_at,productive_state,transition_stage) VALUES(?,?,?,?,?,?,?,?)", (data["identifier"], data.get("breed"), data.get("age_months"), data.get("days_in_milk"), data.get("notes"), created, data.get("productive_state"), data.get("transition_stage")))
        row = conn.execute("SELECT * FROM animals WHERE id=?", (cur.lastrowid,)).fetchone()
    return dict(row)


def list_animals() -> list[dict[str, Any]]:
    with closing(connect()) as conn, conn:
        return [dict(row) for row in conn.execute("SELECT * FROM animals ORDER BY identifier COLLATE NOCASE")]


def animal_exists(animal_id: int) -> bool:
    with closing(connect()) as conn, conn:
        return conn.execute("SELECT 1 FROM animals WHERE id=?", (animal_id,)).fetchone() is not None


def save_assessment(animal_id: int | None, answers: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    created = datetime.now(timezone.utc).isoformat()
    with closing(connect()) as conn, conn:
        cur = conn.execute("INSERT INTO assessments(animal_id,created_at,answers_json,result_json) VALUES(?,?,?,?)", (animal_id, created, json.dumps(answers, ensure_ascii=False), json.dumps(result, ensure_ascii=False)))
        row = conn.execute("SELECT * FROM assessments WHERE id=?", (cur.lastrowid,)).fetchone()
    return _assessment(row)


def _assessment(row: sqlite3.Row) -> dict[str, Any]:
    return {"id": row["id"], "animal_id": row["animal_id"], "created_at": row["created_at"], "answers": json.loads(row["answers_json"]), "result": json.loads(row["result_json"]), "follow_up": row["follow_up"]}


def list_assessments(animal_id: int | None = None) -> list[dict[str, Any]]:
    with closing(connect()) as conn, conn:
        if animal_id is None:
            rows = conn.execute("SELECT * FROM assessments ORDER BY created_at DESC")
        else:
            rows = conn.execute("SELECT * FROM assessments WHERE animal_id=? ORDER BY created_at DESC", (animal_id,))
        return [_assessment(row) for row in rows]


def get_assessment(assessment_id: int) -> dict[str, Any] | None:
    with closing(connect()) as conn, conn:
        row = conn.execute("SELECT * FROM assessments WHERE id=?", (assessment_id,)).fetchone()
    return _assessment(row) if row else None


def update_follow_up(assessment_id: int, follow_up: str) -> dict[str, Any] | None:
    with closing(connect()) as conn, conn:
        conn.execute("UPDATE assessments SET follow_up=? WHERE id=?", (follow_up, assessment_id))
    return get_assessment(assessment_id)
