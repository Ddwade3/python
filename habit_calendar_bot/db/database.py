from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "habit_tracker.db"


class Database:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS habits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('DO', 'AVOID')),
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS marks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id INTEGER NOT NULL,
                    day TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(habit_id, day),
                    FOREIGN KEY(habit_id) REFERENCES habits(id)
                );
                """
            )

    def ensure_user_with_default_habit(self, telegram_id: int) -> int:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
            ).fetchone()
            if row:
                user_id = int(row["id"])
            else:
                cur = conn.execute(
                    "INSERT INTO users (telegram_id, created_at) VALUES (?, ?)",
                    (telegram_id, now),
                )
                user_id = int(cur.lastrowid)

            habits_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM habits WHERE user_id = ?", (user_id,)
            ).fetchone()["cnt"]
            if habits_count == 0:
                conn.execute(
                    "INSERT INTO habits (user_id, name, type, created_at) VALUES (?, ?, ?, ?)",
                    (user_id, "Моя привычка", "DO", now),
                )
        return user_id

    def get_user_id(self, telegram_id: int) -> int | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
            ).fetchone()
            return int(row["id"]) if row else None

    def add_habit(self, user_id: int, name: str, habit_type: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO habits (user_id, name, type, created_at) VALUES (?, ?, ?, ?)",
                (user_id, name, habit_type, datetime.utcnow().isoformat()),
            )

    def list_habits(self, user_id: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, type FROM habits WHERE user_id = ? ORDER BY id", (user_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    def get_habit(self, habit_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, user_id, name, type FROM habits WHERE id = ?", (habit_id,)
            ).fetchone()
            return dict(row) if row else None

    def upsert_mark(self, habit_id: int, day: date, status: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO marks (habit_id, day, status, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(habit_id, day)
                DO UPDATE SET status = excluded.status, created_at = excluded.created_at
                """,
                (habit_id, day.isoformat(), status, datetime.utcnow().isoformat()),
            )

    def get_mark(self, habit_id: int, day: date) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT status FROM marks WHERE habit_id = ? AND day = ?",
                (habit_id, day.isoformat()),
            ).fetchone()
            return str(row["status"]) if row else None

    def list_marks(self, habit_id: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT day, status FROM marks WHERE habit_id = ? ORDER BY day",
                (habit_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_marks_for_period(
        self, habit_id: int, days_back: int = 14
    ) -> list[dict[str, Any]]:
        start = (date.today() - timedelta(days=days_back - 1)).isoformat()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT day, status
                FROM marks
                WHERE habit_id = ? AND day >= ?
                ORDER BY day
                """,
                (habit_id, start),
            ).fetchall()
            return [dict(row) for row in rows]
