# Habit Calendar Bot (Telegram, BOT-only)

Минимальный Telegram habit-tracker на Python + aiogram + SQLite.

## Функции MVP
- Привычки типов:
  - `DO` (делаю): `DONE` / `SKIP`
  - `AVOID` (не делаю): `CLEAN` / `SLIP`
- `/start` показывает меню:
  - Отметить сегодня
  - Календарь
  - Прогресс
  - Награды
  - Настройки
- Отметка сегодня: выбор привычки (если их несколько) + 1 tap по inline-кнопке статуса.
- SQLite база в файле `habit_tracker.db` в корне проекта.
- Награды v0:
  - За общее число `DONE/CLEAN`: 7, 14, 30, 60, 100
  - За серию подряд `DONE/CLEAN`: 7, 14, 30
  - Камбэк: `DONE/CLEAN` на следующий день после `SLIP/SKIP`

## Структура

```text
habit_calendar_bot/
  main.py
  requirements.txt
  .env.example
  README.md
  db/
    __init__.py
    database.py
  handlers/
    __init__.py
    menu.py
    start.py
  services/
    __init__.py
    habit_logic.py
```

## Запуск

1) Создай и активируй venv:

```bash
python -m venv .venv
source .venv/bin/activate
```

2) Установи зависимости:

```bash
pip install -r requirements.txt
```

3) Создай `.env`:

```bash
cp .env.example .env
```

Открой `.env` и вставь реальный токен:

```env
BOT_TOKEN=123456:ABC...
```

4) Запусти бота:

```bash
python main.py
```

## Использование

- Открой бота в Telegram, отправь `/start`.
- Добавление новой привычки:

```text
/add_habit DO Читать 20 минут
/add_habit AVOID Сахар
```

- Нажимай кнопки меню, чтобы ставить отметки и смотреть календарь/прогресс/награды.
