from __future__ import annotations

from datetime import date

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from db.database import Database
from handlers.menu import main_menu_keyboard
from services.habit_logic import (
    allowed_statuses,
    calendar_text,
    current_streak,
    total_positive,
    unlocked_awards,
)

router = Router()

db = Database()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    db.ensure_user_with_default_habit(message.from_user.id)
    text = (
        "Привет! Я habit-tracker бот.\n\n"
        "Выбирай действие в меню ниже.\n"
        "Подсказка: /add_habit DO Читать 20 минут"
    )
    await message.answer(text, reply_markup=main_menu_keyboard())


@router.message(Command("add_habit"))
async def cmd_add_habit(message: Message, command: CommandObject) -> None:
    user_id = db.ensure_user_with_default_habit(message.from_user.id)
    if not command.args:
        await message.answer("Формат: /add_habit <DO|AVOID> <название>")
        return

    parts = command.args.split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Нужно 2 части: тип и название. Пример: /add_habit AVOID Сахар")
        return

    habit_type = parts[0].upper()
    name = parts[1].strip()
    if habit_type not in {"DO", "AVOID"}:
        await message.answer("Тип должен быть DO или AVOID")
        return

    db.add_habit(user_id=user_id, name=name, habit_type=habit_type)
    await message.answer(f"Добавил привычку: {name} ({habit_type})")


@router.message(F.text == "Отметить сегодня")
async def mark_today(message: Message) -> None:
    user_id = db.ensure_user_with_default_habit(message.from_user.id)
    habits = db.list_habits(user_id)

    if not habits:
        await message.answer("У тебя пока нет привычек. Добавь через /add_habit")
        return

    if len(habits) == 1:
        await show_status_buttons(message, habits[0]["id"])
        return

    buttons = [
        [
            InlineKeyboardButton(
                text=f"{habit['name']} ({habit['type']})",
                callback_data=f"pick_habit:{habit['id']}",
            )
        ]
        for habit in habits
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выбери привычку:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("pick_habit:"))
async def pick_habit(callback: CallbackQuery) -> None:
    habit_id = int(callback.data.split(":")[1])
    await show_status_buttons(callback.message, habit_id)
    await callback.answer()


async def show_status_buttons(message: Message, habit_id: int) -> None:
    habit = db.get_habit(habit_id)
    if not habit:
        await message.answer("Привычка не найдена")
        return

    statuses = allowed_statuses(habit["type"])
    buttons = [
        [
            InlineKeyboardButton(
                text=status,
                callback_data=f"mark:{habit_id}:{status}",
            )
            for status in statuses
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(
        f"Отметка на сегодня для: {habit['name']} ({habit['type']})",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("mark:"))
async def save_mark(callback: CallbackQuery) -> None:
    _, habit_id_raw, status = callback.data.split(":")
    habit_id = int(habit_id_raw)
    habit = db.get_habit(habit_id)
    if not habit:
        await callback.answer("Привычка не найдена", show_alert=True)
        return

    if status not in allowed_statuses(habit["type"]):
        await callback.answer("Некорректный статус", show_alert=True)
        return

    db.upsert_mark(habit_id, date.today(), status)
    marks = db.list_marks(habit_id)
    awards = unlocked_awards(marks, habit["type"])
    streak = current_streak(marks, habit["type"])

    text = f"Сохранил: {habit['name']} — {status}\nТекущая серия: {streak}"
    if awards:
        text += "\n\nНаграды:\n" + "\n".join(f"• {item}" for item in awards)

    await callback.message.answer(text)
    await callback.answer("Готово")


@router.message(F.text == "Календарь")
async def show_calendar(message: Message) -> None:
    user_id = db.ensure_user_with_default_habit(message.from_user.id)
    habits = db.list_habits(user_id)
    chunks: list[str] = []

    for habit in habits:
        marks = db.list_marks_for_period(habit["id"], days_back=14)
        chunks.append(calendar_text(habit["name"], marks))

    await message.answer("\n\n".join(chunks))


@router.message(F.text == "Прогресс")
async def show_progress(message: Message) -> None:
    user_id = db.ensure_user_with_default_habit(message.from_user.id)
    habits = db.list_habits(user_id)
    lines = ["📈 Прогресс:"]

    for habit in habits:
        marks = db.list_marks(habit["id"])
        total = total_positive(marks)
        streak = current_streak(marks, habit["type"])
        lines.append(f"• {habit['name']} ({habit['type']}): total={total}, streak={streak}")

    await message.answer("\n".join(lines))


@router.message(F.text == "Награды")
async def show_awards(message: Message) -> None:
    user_id = db.ensure_user_with_default_habit(message.from_user.id)
    habits = db.list_habits(user_id)
    lines = ["🏆 Награды:"]

    for habit in habits:
        marks = db.list_marks(habit["id"])
        awards = unlocked_awards(marks, habit["type"])
        lines.append(f"\n{habit['name']} ({habit['type']}):")
        if awards:
            lines.extend(f"• {item}" for item in awards)
        else:
            lines.append("• Пока нет наград")

    await message.answer("\n".join(lines))


@router.message(F.text == "Настройки")
async def show_settings(message: Message) -> None:
    user_id = db.ensure_user_with_default_habit(message.from_user.id)
    habits = db.list_habits(user_id)
    lines = [
        "⚙️ Настройки",
        "Добавить привычку: /add_habit <DO|AVOID> <название>",
        "Текущие привычки:",
    ]
    lines.extend(f"• {h['name']} ({h['type']})" for h in habits)
    await message.answer("\n".join(lines))
