import aiosqlite
import asyncio
import json
import os

DB = "bot.db"
JSON_FILE = "tests_full.json"
MATERIALS_DIR = "study_materials"

async def init_db():
    if not os.path.exists(JSON_FILE):
        print(f"Ошибка: файл {JSON_FILE} не найден!")
        return

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        tests_by_level = json.load(f)

    async with aiosqlite.connect(DB) as db:
        # Удаляем старую таблицу tests (если есть)
        await db.execute("DROP TABLE IF EXISTS tests")
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

        # Вставляем данные
        for level, tests in tests_by_level.items():
            for t in tests:
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

        # Таблица пользователей для монет и жизней
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            coins INTEGER DEFAULT 50,
            correct_answers INTEGER DEFAULT 0,
            lives INTEGER DEFAULT 3,
            streak INTEGER DEFAULT 0
        )
        """)
     # --- Создание таблиц для методичек ---
        await db.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_materials (
            user_id INTEGER,
            material_id INTEGER,
            studied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, material_id)
        )
        """)
        await db.commit()

        # --- Заполнение таблицы materials, если она пуста ---
        cursor = await db.execute("SELECT COUNT(*) FROM materials")
        count = (await cursor.fetchone())[0]
        if count == 0 and os.path.exists(MATERIALS_DIR):
            files = [f for f in os.listdir(MATERIALS_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            for filename in files:
                await db.execute("INSERT OR IGNORE INTO materials (filename) VALUES (?)", (filename,))
            await db.commit()
            print(f"✅ Добавлено {len(files)} методичек в таблицу materials")

        await db.commit()

    total = sum(len(t) for t in tests_by_level.values())
    print(f"✅ База {DB} обновлена: {total} тестов")
    for level, tests in tests_by_level.items():
        print(f"   {level}: {len(tests)}")

if __name__ == "__main__":
    asyncio.run(init_db())
