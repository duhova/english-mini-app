import aiosqlite

DB_WORDS = "db.sqlite3"   # база со словами и жизнями слов
DB_TESTS = "bot.db"       # база с тестами и жизнями для грамматики

# ======================================================
# ИНИЦИАЛИЗАЦИЯ ТАБЛИЦЫ СЛОВ (если не существует)
# ======================================================
async def init_words_db():
    """Создаёт таблицу words в db.sqlite3, если её нет"""
    async with aiosqlite.connect(DB_WORDS) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                transcription TEXT NOT NULL,
                translation TEXT NOT NULL,
                example_english TEXT NOT NULL,
                example_russian TEXT NOT NULL,
                level TEXT NOT NULL
            )
        ''')
        await db.commit()

# ======================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ СО СЛОВАМИ
# ======================================================
async def get_random_word(level=None):
    """Получение случайного слова (асинхронно)"""
    async with aiosqlite.connect(DB_WORDS) as db:
        if level:
            cursor = await db.execute(
                'SELECT * FROM words WHERE level=? ORDER BY RANDOM() LIMIT 1',
                (level,)
            )
        else:
            cursor = await db.execute('SELECT * FROM words ORDER BY RANDOM() LIMIT 1')
        return await cursor.fetchone()

async def get_words_by_level(level, limit=10):
    """Получение слов по уровню"""
    async with aiosqlite.connect(DB_WORDS) as db:
        cursor = await db.execute(
            'SELECT * FROM words WHERE level=? LIMIT ?',
            (level, limit)
        )
        return await cursor.fetchall()

async def add_word(word_data):
    """Добавление слова в базу"""
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
# ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ (монеты, жизни, стрик)
# ======================================================
async def get_user(user_id: int):
    """Получить данные пользователя из таблицы users (bot.db)"""
    async with aiosqlite.connect(DB_TESTS) as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return await cursor.fetchone()

async def add_coins(user_id: int, amount: int):
    """Добавить монеты пользователю"""
    async with aiosqlite.connect(DB_TESTS) as db:
        await db.execute("UPDATE users SET coins = coins + ? WHERE user_id=?", (amount, user_id))
        await db.commit()

async def lose_life(user_id: int):
    """Уменьшить жизнь пользователя на 1 (для грамматических тестов)"""
    async with aiosqlite.connect(DB_TESTS) as db:
        await db.execute("UPDATE users SET lives = lives - 1 WHERE user_id=?", (user_id,))
        await db.commit()

async def increment_streak(user_id: int):
    """Увеличить streak (серию правильных ответов)"""
    async with aiosqlite.connect(DB_TESTS) as db:
        await db.execute("UPDATE users SET streak = streak + 1 WHERE user_id=?", (user_id,))
        await db.commit()

async def reset_streak(user_id: int):
    """Сбросить streak"""
    async with aiosqlite.connect(DB_TESTS) as db:
        await db.execute("UPDATE users SET streak = 0 WHERE user_id=?", (user_id,))
        await db.commit()

# ======================================================
# ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ ТЕСТА ПО ID (если понадобится)
# ======================================================
async def get_test(test_id: int):
    """Получить тест по его id из таблицы tests (bot.db)"""
    async with aiosqlite.connect(DB_TESTS) as db:
        cursor = await db.execute("SELECT * FROM tests WHERE id=?", (test_id,))
        return await cursor.fetchone()
