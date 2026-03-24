import aiosqlite
import random

DB_WORDS = "db.sqlite3"   # база со словами и жизнями слов
DB_TESTS = "bot.db"       # база с тестами и жизнями для грамматики

# ======================================================
# ФУНКЦИИ ДЛЯ СЛОВ
# ======================================================
async def get_random_word(level=None):
    async with aiosqlite.connect(DB_WORDS) as db:
        if level:
            cursor = await db.execute('SELECT * FROM words WHERE level=? ORDER BY RANDOM() LIMIT 1', (level,))
        else:
            cursor = await db.execute('SELECT * FROM words ORDER BY RANDOM() LIMIT 1')
        return await cursor.fetchone()

async def get_words_by_level(level, limit=10):
    async with aiosqlite.connect(DB_WORDS) as db:
        cursor = await db.execute('SELECT * FROM words WHERE level=? LIMIT ?', (level, limit))
        return await cursor.fetchall()

async def add_word(word_data):
    async with aiosqlite.connect(DB_WORDS) as db:
        await db.execute('''
            INSERT INTO words (word, transcription, translation,
                               example_english, example_russian, level)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            word_data['word'],
            word_data['transcription'],
            word_data['translation'],
            word_data['example_english'],
            word_data['example_russian'],
            word_data['level']
        ))
        await db.commit()

# ======================================================
# ФУНКЦИИ ДЛЯ МЕТОДИЧЕК
# ======================================================
async def get_unstudied_material(user_id: int):
    async with aiosqlite.connect(DB_TESTS) as db:
        cursor = await db.execute("""
            SELECT m.id, m.filename
            FROM materials m
            WHERE NOT EXISTS (
                SELECT 1 FROM user_materials um
                WHERE um.user_id = ? AND um.material_id = m.id
            )
        """, (user_id,))
        materials = await cursor.fetchall()
        if not materials:
            return None
        return random.choice(materials)

async def mark_material_studied(user_id: int, material_id: int):
    async with aiosqlite.connect(DB_TESTS) as db:
        await db.execute("INSERT OR IGNORE INTO user_materials (user_id, material_id) VALUES (?, ?)",
                         (user_id, material_id))
        await db.commit()

# ======================================================
# ФУНКЦИИ ДЛЯ МОНЕТ
# ======================================================
async def add_coins(user_id: int, amount: int):
    async with aiosqlite.connect(DB_TESTS) as db:
        await db.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

async def spend_coins(user_id: int, amount: int) -> bool:
    async with aiosqlite.connect(DB_TESTS) as db:
        cursor = await db.execute("SELECT coins FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row and row[0] >= amount:
            await db.execute("UPDATE users SET coins = coins - ? WHERE user_id = ?", (amount, user_id))
            await db.commit()
            return True
        return False

# ======================================================
# ФУНКЦИИ ДЛЯ ЖИЗНЕЙ (грамматические тесты)
# ======================================================
async def get_lives(user_id: int) -> int:
    async with aiosqlite.connect(DB_TESTS) as db:
        cursor = await db.execute("SELECT lives FROM user_lives WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return row[0]
        else:
            await db.execute("INSERT INTO user_lives (user_id, lives) VALUES (?, 3)", (user_id,))
            await db.commit()
            return 3

async def decrease_life(user_id: int) -> int:
    lives = await get_lives(user_id)
    if lives > 0:
        lives -= 1
        async with aiosqlite.connect(DB_TESTS) as db:
            await db.execute("UPDATE user_lives SET lives=? WHERE user_id=?", (lives, user_id))
            await db.commit()
    return lives

async def increase_life(user_id: int, amount: int = 1, max_lives: int = 3):
    lives = await get_lives(user_id)
    new_lives = min(lives + amount, max_lives)
    async with aiosqlite.connect(DB_TESTS) as db:
        await db.execute("UPDATE user_lives SET lives=? WHERE user_id=?", (new_lives, user_id))
        await db.commit()
    return new_lives

# ======================================================
# ФУНКЦИИ ДЛЯ ЖИЗНЕЙ (тесты на перевод слов)
# ======================================================
async def get_word_lives(user_id: int) -> int:
    async with aiosqlite.connect(DB_WORDS) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS word_lives (
            user_id INTEGER PRIMARY KEY,
            lives INTEGER DEFAULT 3
        )
        """)
        cursor = await db.execute("SELECT lives FROM word_lives WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return row[0]
        else:
            await db.execute("INSERT INTO word_lives (user_id, lives) VALUES (?, 3)", (user_id,))
            await db.commit()
            return 3

async def decrease_word_life(user_id: int) -> int:
    lives = await get_word_lives(user_id)
    if lives > 0:
        lives -= 1
        async with aiosqlite.connect(DB_WORDS) as db:
            await db.execute("UPDATE word_lives SET lives=? WHERE user_id=?", (lives, user_id))
            await db.commit()
    return lives

async def increase_word_life(user_id: int, amount: int = 1, max_lives: int = 3):
    lives = await get_word_lives(user_id)
    new_lives = min(lives + amount, max_lives)
    async with aiosqlite.connect(DB_WORDS) as db:
        await db.execute("UPDATE word_lives SET lives=? WHERE user_id=?", (new_lives, user_id))
        await db.commit()
    return new_lives

# ======================================================
# ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ ТЕСТА ПО ID (если понадобится)
# ======================================================
async def get_test(test_id: int):
    async with aiosqlite.connect(DB_TESTS) as db:
        cursor = await db.execute("SELECT * FROM tests WHERE id=?", (test_id,))
        return await cursor.fetchone()
