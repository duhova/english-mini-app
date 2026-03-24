import aiosqlite
import asyncio
import json
import os

DB = "bot.db"
JSON_FILE = "tests_full.json"

async def init_db():
    if not os.path.exists(JSON_FILE):
        print(f"Ошибка: файл {JSON_FILE} не найден!")
        return

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        tests_by_level = json.load(f)

    async with aiosqlite.connect(DB) as db:
        # Удаляем старую таблицу tests (если есть)
        await db.execute("DROP TABLE IF EXISTS tests")

        # Создаём новую таблицу со всеми нужными полями
        await db.execute("""
        CREATE TABLE tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            question TEXT,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            correct INTEGER,
            hint TEXT,
            explanation TEXT
        )
        """)

        # Вставляем данные из JSON
        for level, tests in tests_by_level.items():
            for t in tests:
                # В JSON correct хранится как 0,1,2 → в базе будет 1,2,3
                correct_num = t['correct'] + 1
                await db.execute("""
                    INSERT INTO tests (level, question, option_a, option_b, option_c, correct, hint, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    level,
                    t['question'],
                    t['options'][0],
                    t['options'][1],
                    t['options'][2],
                    correct_num,
                    t.get('hint', ''),
                    t.get('explanation', '')
                ))

        # Таблица для жизней (оставляем как есть)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_lives (
            user_id INTEGER PRIMARY KEY,
            lives INTEGER DEFAULT 3
        )
        """)

        await db.commit()

    total = sum(len(t) for t in tests_by_level.values())
    print(f"✅ База {DB} обновлена: {total} тестов")
    for level, tests in tests_by_level.items():
        print(f"   {level}: {len(tests)}")

if __name__ == "__main__":
    asyncio.run(init_db())