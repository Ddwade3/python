from __future__ import annotations

from datetime import date, timedelta

POSITIVE_BY_TYPE = {
    "DO": "DONE",
    "AVOID": "CLEAN",
}

NEGATIVE_BY_TYPE = {
    "DO": "SKIP",
    "AVOID": "SLIP",
}

SYMBOLS = {
    "DONE": "✅",
    "CLEAN": "🟢",
    "SKIP": "⏭️",
    "SLIP": "🔴",
    "NONE": "▫️",
}

TOTAL_MILESTONES = [7, 14, 30, 60, 100]
STREAK_MILESTONES = [7, 14, 30]


def allowed_statuses(habit_type: str) -> list[str]:
    if habit_type == "DO":
        return ["DONE", "SKIP"]
    return ["CLEAN", "SLIP"]


def total_positive(marks: list[dict]) -> int:
    return sum(1 for item in marks if item["status"] in {"DONE", "CLEAN"})


def current_streak(marks: list[dict], habit_type: str) -> int:
    positive = POSITIVE_BY_TYPE[habit_type]
    by_day = {item["day"]: item["status"] for item in marks}

    streak = 0
    cursor = date.today()
    while True:
        status = by_day.get(cursor.isoformat())
        if status == positive:
            streak += 1
            cursor -= timedelta(days=1)
            continue
        break
    return streak


def is_comeback(marks: list[dict], habit_type: str) -> bool:
    positive = POSITIVE_BY_TYPE[habit_type]
    negative = NEGATIVE_BY_TYPE[habit_type]
    by_day = {item["day"]: item["status"] for item in marks}
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    return by_day.get(today) == positive and by_day.get(yesterday) == negative


def unlocked_awards(marks: list[dict], habit_type: str) -> list[str]:
    positive_total = total_positive(marks)
    streak = current_streak(marks, habit_type)

    awards: list[str] = []
    for target in TOTAL_MILESTONES:
        if positive_total >= target:
            awards.append(f"🏅 Всего полезных отметок: {target}")

    for target in STREAK_MILESTONES:
        if streak >= target:
            awards.append(f"🔥 Серия подряд: {target}")

    if is_comeback(marks, habit_type):
        awards.append("↩️ Камбэк: после срыва/пропуска снова в строю")

    return awards


def calendar_text(habit_name: str, marks_period: list[dict]) -> str:
    by_day = {item["day"]: item["status"] for item in marks_period}
    lines = [f"📅 {habit_name} (последние 14 дней)"]
    for i in range(13, -1, -1):
        day = date.today() - timedelta(days=i)
        status = by_day.get(day.isoformat(), "NONE")
        lines.append(f"{day.strftime('%d.%m')}: {SYMBOLS[status]} {status}")
    return "\n".join(lines)
