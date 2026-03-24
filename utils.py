import aiosqlite

DB_NAME = "db.sqlite3"


async def init_db():
    """Инициализация всех таблиц базы данных"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Таблица уроков
        await db.execute('''
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                language TEXT NOT NULL,
                level TEXT NOT NULL,
                content TEXT NOT NULL
            )
        ''')

        # Таблица тестов
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                language TEXT NOT NULL,
                level TEXT NOT NULL,
                question TEXT NOT NULL,
                options TEXT NOT NULL,
                answer TEXT NOT NULL
            )
        ''')

        # Таблица слов
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

        # Таблица слов с языком
        await db.execute('''
              CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                transcription TEXT NOT NULL,
                translation TEXT NOT NULL,
                example_english TEXT NOT NULL,
                example_russian TEXT NOT NULL,
                level TEXT NOT NULL,
                language TEXT DEFAULT 'Английский'
            )
         ''')

        # Таблица статистики
        await db.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                user_id INTEGER,
                language TEXT,
                level TEXT,
                completed_lessons INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, language, level)
            )
        ''')

        await db.commit()

import sqlite3

def get_user(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def add_coins(user_id, amount):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET coins = coins + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def lose_life(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET lives = lives - 1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def restore_life(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET lives = lives + 1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def increment_streak(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET streak = streak + 1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def reset_streak(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET streak = 0 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close() 
    
async def get_random_word(level=None):
    """Получение случайного слова"""
    async with aiosqlite.connect(DB_NAME) as db:
        if level:
            cursor = await db.execute('SELECT * FROM words WHERE level=? ORDER BY RANDOM() LIMIT 1', (level,))
        else:
            cursor = await db.execute('SELECT * FROM words ORDER BY RANDOM() LIMIT 1')
        return await cursor.fetchone()


async def get_words_by_level(level, limit=10):
    """Получение слов по уровню"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('SELECT * FROM words WHERE level=? LIMIT ?', (level, limit))
        results = await cursor.fetchall()
        return results


async def add_word(word_data):
    """Добавление слова в базу"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO words (word, transcription, translation, example_english, example_russian, level)
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