import aiosqlite
import os
import asyncio
import json
import random
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, CallbackQuery, InlineKeyboardMarkup, WebAppInfo, FSInputFile
from aiogram import F

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8538737346:AAHRcw-saKM8HIvdNjduyj0y8Ikg7MV47JY"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
import time
last_material_request = {}
MAX_DAILY_MATERIALS = 5 


# ЖИЗНИ ДЛЯ ГРАММАТИЧЕСКИХ ТЕСТОВ (таблица user_lives)
# ======================================================
async def get_lives(user_id: int) -> int:
    async with aiosqlite.connect(TESTS_DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_lives (
            user_id INTEGER PRIMARY KEY,
            lives INTEGER DEFAULT 3
        )
        """)
        await db.execute("INSERT OR IGNORE INTO user_lives (user_id, lives) VALUES (?, 3)", (user_id,))
        await db.commit()   # добавим commit
        cursor = await db.execute("SELECT lives FROM user_lives WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        lives = row[0] if row else 3
        print(f"DEBUG: get_lives for user {user_id} = {lives}")
        return lives

async def decrease_life(user_id: int) -> int:
    lives = await get_lives(user_id)
    print(f"DEBUG: lives before = {lives}")
    if lives > 0:
        lives -= 1
        async with aiosqlite.connect(TESTS_DB) as db:
            await db.execute("UPDATE user_lives SET lives=? WHERE user_id=?", (lives, user_id))
            await db.commit()
            # Проверка
            cursor = await db.execute("SELECT lives FROM user_lives WHERE user_id=?", (user_id,))
            row = await cursor.fetchone()
            print(f"DEBUG: after update, lives in db = {row[0] if row else None}")
    return lives

async def reset_lives(user_id: int):
    """Сбросить жизни до 3"""
    async with aiosqlite.connect(TESTS_DB) as db:
        await db.execute("UPDATE user_lives SET lives=3 WHERE user_id=?", (user_id,))
        await db.commit()

# ======================================================
# ЖИЗНИ ДЛЯ ТЕСТА НА ПЕРЕВОД СЛОВ (таблица в WORDS_DB)
# ======================================================
async def get_word_lives(user_id: int) -> int:
    async with aiosqlite.connect(WORDS_DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS word_users (
            user_id INTEGER PRIMARY KEY,
            coins INTEGER DEFAULT 50,
            lives INTEGER DEFAULT 3
        )
        """)
        await db.execute("INSERT OR IGNORE INTO word_users (user_id, coins, lives) VALUES (?, 50, 3)", (user_id,))
        await db.commit()
        cursor = await db.execute("SELECT lives FROM word_users WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 3

async def decrease_word_life(user_id: int) -> int:
    lives = await get_word_lives(user_id)
    if lives > 0:
        lives -= 1
        async with aiosqlite.connect(WORDS_DB) as db:
            await db.execute("UPDATE word_users SET lives = ? WHERE user_id = ?", (lives, user_id))
            await db.commit()
    return lives

async def reset_word_lives(user_id: int):
    async with aiosqlite.connect(WORDS_DB) as db:
        await db.execute("UPDATE word_users SET lives = 3 WHERE user_id = ?", (user_id,))
        await db.commit()
        
async def increase_word_life(user_id: int, amount: int = 1, max_lives: int = 3) -> int:
    lives = await get_word_lives(user_id)
    new_lives = min(lives + amount, max_lives)
    async with aiosqlite.connect(WORDS_DB) as db:
        await db.execute("UPDATE word_users SET lives=? WHERE user_id=?", (new_lives, user_id))
        await db.commit()
    return new_lives

async def reset_lives(user_id: int):
    """Сбросить жизни до 3"""
    async with aiosqlite.connect(TESTS_DB) as db:
        await db.execute("UPDATE user_lives SET lives=3 WHERE user_id=?", (user_id,))
        await db.commit()

# ======================================================
# КОМАНДА /lives
# ======================================================
@dp.message(Command("lives"))
async def show_lives(message: types.Message):
    try:
        user_id = message.from_user.id
        grammar_lives = await get_lives(user_id)
        word_lives = await get_word_lives(user_id)

        await message.answer(
            f"❤️ Жизни для грамматических тестов: {grammar_lives}\n"
            f"📝 Жизни для перевода слов: {word_lives}"
        )

        if grammar_lives == 0:
            await reset_lives(user_id)
            await message.answer("💡 Жизни для грамматики восстановлены до 3.")

        if word_lives == 0:
            await reset_word_lives(user_id)
            await message.answer("💡 Жизни для перевода слов восстановлены до 3.")
    except Exception as e:
        logger.error(f"Ошибка в /lives: {e}")
        await message.answer("Произошла ошибка.")
async def increase_life(user_id: int, amount: int = 1, max_lives: int = 3) -> int:
    """Увеличить количество жизней (грамматика) до max_lives."""
    async with aiosqlite.connect(TESTS_DB) as db:
        # Убедимся, что запись существует
        await db.execute("INSERT OR IGNORE INTO user_lives (user_id, lives) VALUES (?, 3)", (user_id,))
        cursor = await db.execute("SELECT lives FROM user_lives WHERE user_id=?", (user_id,))
        lives = (await cursor.fetchone())[0]
        new_lives = min(lives + amount, max_lives)
        await db.execute("UPDATE user_lives SET lives=? WHERE user_id=?", (new_lives, user_id))
        await db.commit()
        return new_lives

async def increase_word_life(user_id: int, amount: int = 1, max_lives: int = 3) -> int:
    """Увеличить количество жизней для слов."""
    async with aiosqlite.connect(WORDS_DB) as db:
        # Убедимся, что таблица и запись существуют
        await db.execute("""
        CREATE TABLE IF NOT EXISTS word_lives (
            user_id INTEGER PRIMARY KEY,
            lives INTEGER DEFAULT 3
        )
        """)
        await db.execute("INSERT OR IGNORE INTO word_lives (user_id, lives) VALUES (?, 3)", (user_id,))
        cursor = await db.execute("SELECT lives FROM word_lives WHERE user_id=?", (user_id,))
        lives = (await cursor.fetchone())[0]
        new_lives = min(lives + amount, max_lives)
        await db.execute("UPDATE word_lives SET lives=? WHERE user_id=?", (new_lives, user_id))
        await db.commit()
        return new_lives
           
LEVELS = ["Начальный", "Средний", "Продвинутый"]


# FSM
class UserState(StatesGroup):
    learning_words = State()
    waiting_for_test_answer = State()
    grammar_select_level = State()
    grammar_waiting_answer = State()
    selecting_word_level = State()
    selecting_mini_app_level = State()


# ======================================================
# КОНФИГУРАЦИЯ БАЗ ДАННЫХ
# ======================================================
WORDS_DB = "db.sqlite3"  # База со словами
TESTS_DB = "bot.db"
MATERIALS_DIR = "study_materials"      # База с тестами

# -------------------- Инициализация при запуске --------------------
async def init_databases():
    # Просто убеждаемся, что таблицы users и user_lives существуют
    async with aiosqlite.connect(TESTS_DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            coins INTEGER DEFAULT 50,
            correct_answers INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_lives (
            user_id INTEGER PRIMARY KEY,
            lives INTEGER DEFAULT 3
        )
        """)
        # ... и таблицы материалов уже созданы в db_init, но добавим для безопасности
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
        # Заполнить материалы из папки, если папка существует
        if os.path.exists(MATERIALS_DIR):
            files = [f for f in os.listdir(MATERIALS_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            for fname in files:
                await db.execute("INSERT OR IGNORE INTO materials (filename) VALUES (?)", (fname,))
        await db.commit()

    # База слов
    async with aiosqlite.connect(WORDS_DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            transcription TEXT,
            translation TEXT NOT NULL,
            example_english TEXT,
            example_russian TEXT,
            level TEXT
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS word_lives (
            user_id INTEGER PRIMARY KEY,
            lives INTEGER DEFAULT 3
        )
        """)
        await db.commit()
        logger.info(f"База слов {WORDS_DB} проверена")

        # 2. Проверка базы тестов
        async with aiosqlite.connect(TESTS_DB) as db:
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tests'")
            table_exists = await cursor.fetchone()

            if not table_exists:
                logger.warning(f"В базе {TESTS_DB} нет таблицы 'tests'. Запустите db_init.py")
            else:
                cursor = await db.execute("SELECT COUNT(*) FROM tests")
                count = await cursor.fetchone()
                logger.info(f"В базе тестов найдено {count[0]} тестов")

async def get_unstudied_material(user_id: int):
    async with aiosqlite.connect(TESTS_DB) as db:
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
    async with aiosqlite.connect(TESTS_DB) as db:
        await db.execute("INSERT OR IGNORE INTO user_materials (user_id, material_id) VALUES (?, ?)",
                         (user_id, material_id))
        await db.commit()

async def add_coins(user_id: int, amount: int):
    async with aiosqlite.connect(TESTS_DB) as db:
        await db.execute("UPDATE users SET coins = coins + ? WHERE user_id=?", (amount, user_id))
        await db.commit()

async def spend_coins(user_id: int, amount: int) -> bool:
    async with aiosqlite.connect(TESTS_DB) as db:
        cursor = await db.execute("SELECT coins FROM users WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        if row and row[0] >= amount:
            await db.execute("UPDATE users SET coins = coins - ? WHERE user_id=?", (amount, user_id))
            await db.commit()
            return True
        return False
    
async def get_random_word(level=None):
    """Получение случайного слова из базы данных"""
    try:
        if not os.path.exists(WORDS_DB):
            logger.error(f"Файл базы данных {WORDS_DB} не найден!")
            return None

        async with aiosqlite.connect(WORDS_DB) as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='words'"
            )
            table_exists = await cursor.fetchone()
            if not table_exists:
                logger.error(f"Таблица 'words' не найдена в {WORDS_DB}")
                return None

            if level and level in LEVELS:
                cursor = await db.execute(
                    "SELECT id, word, transcription, translation, example_english, example_russian, level FROM words WHERE level = ? ORDER BY RANDOM() LIMIT 1",
                    (level,)
                )
            else:
                cursor = await db.execute(
                    "SELECT id, word, transcription, translation, example_english, example_russian, level FROM words ORDER BY RANDOM() LIMIT 1"
                )

            row = await cursor.fetchone()
            if not row:
                logger.warning(f"Нет слов в базе для уровня: {level}")
                return None

            logger.info(f"Получено слово: {row[1]} (уровень: {row[6]})")
            return row

    except Exception as e:
        logger.error(f"Ошибка при получении слова: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

# ======================================================
# API ДЛЯ МИНИ-АПП (чтобы мини-апп получал тесты)
# ======================================================
async def get_tests_for_mini_app(level=None):
    """Получение тестов для мини-апп"""
    try:
        async with aiosqlite.connect(TESTS_DB) as db:
            if level:
                cursor = await db.execute(
                    "SELECT id, question, option_a, option_b, option_c, correct FROM tests WHERE level = ?",
                    (level,)
                )
            else:
                cursor = await db.execute(
                    "SELECT id, question, option_a, option_b, option_c, correct, level FROM tests"
                )
            tests_data = await cursor.fetchall()

            result = []
            for test in tests_data:
                if level:
                    test_dict = {
                        "id": test[0],
                        "question": test[1],
                        "options": [test[2], test[3], test[4]],
                        "correct": test[5]
                    }
                else:
                    test_dict = {
                        "id": test[0],
                        "question": test[1],
                        "options": [test[2], test[3], test[4]],
                        "correct": test[5],
                        "level": test[6]
                    }
                result.append(test_dict)
            return result
    except Exception as e:
        logger.error(f"Ошибка при получении тестов: {e}")
        return []


# ======================================================
# START
# ======================================================
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or ""

    # Гарантируем, что пользователь есть в таблице users с 50 монетами
    async with aiosqlite.connect(TESTS_DB) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (user_id, username, coins)
            VALUES (?, ?, 50)
        """, (user_id, username))
        await db.commit()
    try:
        await state.clear()

        kb = [
            [types.KeyboardButton(text="Изучать слова")],
            [types.KeyboardButton(text="Грамматические тесты (в боте)")],
            [types.KeyboardButton(text="📱 Тесты в мини-приложении")],
            [types.KeyboardButton(text="📘 Методичка")],
            [types.KeyboardButton(text="💰 Баланс")]
        ]

        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(
            "Привет! Я бот для изучения английского.\n\n"
            "Выбери действие:\n"
            "• Изучать слова - изучение слов с примерами\n"
            "• Грамматические тесты - тесты прямо в боте\n"
            "• Тесты в мини-приложении - интерактивные тесты в WebApp\n"
            "• Методички",
            reply_markup=keyboard
        )
        logger.info(f"Пользователь {message.from_user.id} начал работу с ботом")
    except Exception as e:
        logger.error(f"Ошибка в start: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

# ======================================================
# UNIVERSAL BACK BUTTON (works ALWAYS)
# ======================================================
@dp.message(F.text == "Назад")
async def back_to_main(message: types.Message, state: FSMContext):
    try:
        await state.clear()

        kb = [
            [types.KeyboardButton(text="Изучать слова")],
            [types.KeyboardButton(text="Грамматические тесты (в боте)")],
            [types.KeyboardButton(text="📱 Тесты в мини-приложении")],
            [types.KeyboardButton(text="📘 Методичка")],
            [types.KeyboardButton(text="💰 Баланс")]          # новая кнопка
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("Главное меню:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка в back_to_main: {e}")
        await message.answer("Произошла ошибка.")


# ======================================================
# WORD LEARNING (изучать слова)
# ======================================================
@dp.message(F.text == "Изучать слова")
async def learn_words(message: types.Message, state: FSMContext):
    try:
        kb = [[types.KeyboardButton(text=level)] for level in LEVELS]
        kb.append([types.KeyboardButton(text="Любой уровень")])
        kb.append([types.KeyboardButton(text="Назад")])

        user_id = message.from_user.id
        word_lives = await get_word_lives(user_id)

        await message.answer(
            f"Выберите уровень слов:\n\n❤️ Жизни для теста на перевод слов: {word_lives}",
            reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        )
        await state.set_state(UserState.selecting_word_level)
    except Exception as e:
        logger.error(f"Ошибка в learn_words: {e}")
        await message.answer("Произошла ошибка.")


# Выбор уровня для изучения слов
@dp.message(UserState.selecting_word_level, F.text.in_(LEVELS + ["Любой уровень"]))
async def select_word_level(message: types.Message, state: FSMContext):
    try:
        level = message.text if message.text != "Любой уровень" else None
        await state.update_data(selected_level=level)
        await state.set_state(UserState.learning_words)

        word_data = await get_random_word(level)
        if not word_data:
            async with aiosqlite.connect(WORDS_DB) as db:
                cursor = await db.execute("SELECT COUNT(*) FROM words")
                total_count = (await cursor.fetchone())[0]

                if total_count == 0:
                    await message.answer(
                        "❌ База данных слов пуста!\n\n"
                        "Запустите команду для добавления слов:\n"
                        "`python generate_words.py`"
                    )
                    await state.clear()
                    return
                elif level:
                    cursor = await db.execute("SELECT COUNT(*) FROM words WHERE level = ?", (level,))
                    level_count = (await cursor.fetchone())[0]
                    if level_count == 0:
                        await message.answer(
                            f"❌ Нет слов для уровня '{level}'.\n\n"
                            f"Всего слов в базе: {total_count}\n"
                            f"Доступные уровни можно проверить командой:\n"
                            "`python check_words.py`"
                        )
                        await state.clear()
                        return

            await message.answer(f"❌ Нет слов для уровня '{message.text}'. Попробуйте другой уровень.")
            return

        await show_word(message, state)

    except Exception as e:
        logger.error(f"Ошибка в select_word_level: {e}")
        await message.answer("Произошла ошибка при выборе уровня.")

async def show_word(message: types.Message, state: FSMContext):
    try:
        user_data = await state.get_data()
        level = user_data.get("selected_level")

        word_data = await get_random_word(level)
        if not word_data:
            await message.answer("Нет слов для этого уровня. Добавьте слова в базу данных.")
            return

        word_id, word, transcription, translation, example_en, example_ru, word_level = word_data

        await state.update_data(
            current_word=word,
            current_translation=translation,
            current_word_id=word_id
        )
        user_id = message.from_user.id
        word_lives = await get_word_lives(user_id)

        # Формируем текст слова
        word_text = f"<b>Слово:</b> {word}\n"
        if transcription:
            word_text += f"<b>Транскрипция:</b> {transcription}\n"
        word_text += f"<b>Перевод:</b> {translation}\n"
        if example_en:
            word_text += f"<b>Пример:</b>\n{example_en}\n"
        if example_ru:
            word_text += f"{example_ru}"

        # Добавляем жизни сверху
        final_text = f"❤️ Жизни: {word_lives}\n\n{word_text}"

        kb = [
            [types.KeyboardButton(text="Следующее слово")],
            [types.KeyboardButton(text="Тест на перевод")],
            [types.KeyboardButton(text="Назад")]
        ]

        await message.answer(final_text,
                             reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True),
                             parse_mode="HTML")
        logger.info(f"Показано слово пользователю {message.from_user.id}: {word}")
    except Exception as e:
        logger.error(f"Ошибка в show_word: {e}")
        await message.answer("Произошла ошибка.")

@dp.message(F.text == "💰 Баланс")
async def show_balance(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect(TESTS_DB) as db:
        cursor = await db.execute("SELECT coins FROM users WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        coins = row[0] if row else 0
    await message.answer(f"💰 Ваш баланс: {coins} монет.", parse_mode="HTML")

@dp.message(F.text == "Следующее слово")
async def next_word(message: types.Message, state: FSMContext):
    try:
        await show_word(message, state)
    except Exception as e:
        logger.error(f"Ошибка в next_word: {e}")
        await message.answer("Произошла ошибка.")


@dp.message(F.text == "Тест на перевод")
async def translation_test(message: types.Message, state: FSMContext):
    try:
        user_data = await state.get_data()
        word = user_data.get("current_word")
        correct_translation = user_data.get("current_translation")

        if not word or not correct_translation:
            await message.answer("Ошибка: не найдено текущее слово.")
            return

        async with aiosqlite.connect(WORDS_DB) as db:
            cursor = await db.execute(
                "SELECT translation FROM words WHERE translation != ? ORDER BY RANDOM() LIMIT 3",
                (correct_translation,)
            )
            wrong = [row[0] for row in await cursor.fetchall()]

        while len(wrong) < 3:
            wrong.append("???")

        options = [correct_translation] + wrong
        random.shuffle(options)

        kb = [[types.KeyboardButton(text=o)] for o in options]

        await state.update_data(test_answer=correct_translation)
        await state.set_state(UserState.waiting_for_test_answer)

        await message.answer(
            f"Как переводится слово '{word}'?",
            reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        )
    except Exception as e:
        logger.error(f"Ошибка в translation_test: {e}")
        await message.answer("Произошла ошибка.")


@dp.message(UserState.waiting_for_test_answer)
async def check_test_answer(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        user_answer = message.text
        correct_answer = data.get("test_answer")
        user_id = message.from_user.id

        if user_answer == correct_answer:
            await add_coins(user_id, 5)
            await message.answer("✅ Правильно! +5 монет!")
        else:
            lives_left = await decrease_word_life(user_id)
            if lives_left > 0:
                await message.answer(
                    f"❌ Неправильно. Правильный ответ: {correct_answer}\n"
                    f"❤️ Осталось жизней: {lives_left}"
                )
            else:
                # Жизни закончились
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Восстановить жизни (за 10 монет)", callback_data="restore_word_lives")],
                    [InlineKeyboardButton(text="🔁 Выбрать другой уровень слов", callback_data="choose_word_level")],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                ])
                await message.answer(
                    f"❌ Неправильно. Правильный ответ: {correct_answer}\n"
                    f"💀 У вас закончились жизни!",
                    reply_markup=kb
                )
                await state.clear()
                return

        # Возвращаемся к изучению слов
        await state.set_state(UserState.learning_words)
        await state.update_data(test_answer=None)

        kb = [
            [types.KeyboardButton(text="Следующее слово")],
            [types.KeyboardButton(text="Тест на перевод")],
            [types.KeyboardButton(text="Назад")]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("Что дальше?", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка в check_test_answer: {e}")
        await message.answer("Произошла ошибка.")

@dp.message(F.text == "📘 Методичка")
async def study_material(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    now = time.time()

    # 1. Коолдаун 10 секунд между запросами (защита от спама)
    if user_id in last_material_request and now - last_material_request[user_id] < 10:
        await message.answer("⏳ Подождите немного перед следующей методичкой.")
        return
    last_material_request[user_id] = now

    # 2. Проверяем, сколько методичек пользователь уже изучил сегодня
    async with aiosqlite.connect(TESTS_DB) as db:
        cursor = await db.execute("""
            SELECT COUNT(*) FROM user_materials
            WHERE user_id = ? AND date(studied_at) = date('now', 'localtime')
        """, (user_id,))
        today_count = (await cursor.fetchone())[0]

        if today_count >= MAX_DAILY_MATERIALS:
            await message.answer(f"📚 Вы уже изучили {MAX_DAILY_MATERIALS} методичек сегодня. Возвращайтесь завтра!")
            return

        # 3. Получаем случайную неизученную методичку
        cursor = await db.execute("""
            SELECT m.id, m.filename
            FROM materials m
            WHERE NOT EXISTS (
                SELECT 1 FROM user_materials um
                WHERE um.user_id = ? AND um.material_id = m.id
            )
        """, (user_id,))
        material = await cursor.fetchone()

    if not material:
        await message.answer("🎉 Поздравляем! Вы изучили все доступные методички. Скоро добавятся новые!")
        return

    material_id, filename = material
    file_path = os.path.join(MATERIALS_DIR, filename)

    # 4. Отправляем фото
    try:
        photo = FSInputFile(file_path)
        await message.answer_photo(photo, caption="📘 **Изучите методичку**\n\nПосле просмотра вы получите +5 монет.")
    except Exception as e:
        logger.error(f"Ошибка отправки методички: {e}")
        await message.answer("Не удалось загрузить методичку.")
        return

    # 5. Отмечаем изученной и начисляем монеты
    await mark_material_studied(user_id, material_id)
    await add_coins(user_id, 5)

    # 6. Показываем новый баланс
    async with aiosqlite.connect(TESTS_DB) as db:
        cursor = await db.execute("SELECT coins FROM users WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        coins = row[0] if row else 0

    await message.answer(f"✅ +5 монет! Теперь у вас **{coins}** монет.\n\n📊 Сегодня изучено: {today_count + 1}/{MAX_DAILY_MATERIALS}")

    # 7. Возвращаем в главное меню
    await back_to_main(message, state)

# ======================================================
# MINI-APP TESTS (WebApp)
# ======================================================
@dp.message(F.text == "📱 Тесты в мини-приложении")
async def mini_app_tests(message: types.Message, state: FSMContext):
    try:
        kb = [
            [types.KeyboardButton(text="Начальный уровень (мини-апп)")],
            [types.KeyboardButton(text="Средний уровень (мини-апп)")],
            [types.KeyboardButton(text="Продвинутый уровень (мини-апп)")],
            [types.KeyboardButton(text="Назад")]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(
            "Выберите уровень тестов для мини-приложения:\n\n"
            "Мини-приложение откроется в Telegram и будет использовать тесты из базы данных.",
            reply_markup=keyboard
        )
        await state.set_state(UserState.selecting_mini_app_level)
    except Exception as e:
        logger.error(f"Ошибка в mini_app_tests: {e}")
        await message.answer("Произошла ошибка.")


# Выбор уровня для мини-апп
@dp.message(UserState.selecting_mini_app_level, F.text.endswith("(мини-апп)"))
async def select_mini_app_level(message: types.Message, state: FSMContext):
    try:
        text = message.text
        if "Начальный" in text:
            level = "Начальный"
        elif "Средний" in text:
            level = "Средний"
        elif "Продвинутый" in text:
            level = "Продвинутый"
        else:
            level = "Начальный"

        tests = await get_tests_for_mini_app(level)
        if not tests:
            await message.answer(f"❌ Нет тестов для уровня '{level}' в базе данных.")
            return

        user_id = message.from_user.id
        lives = await get_word_lives(user_id)

        web_app_url = f"https://duhova.github.io/english-mini-app/?user_id={user_id}&lives={lives}&level={level}"
        web_app = WebAppInfo(url=web_app_url)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"📱 Открыть тесты ({level})",
                    web_app=web_app
                )]
            ]
        )

        await message.answer(
            f"✅ Найдено {len(tests)} тестов для уровня '{level}'.\n\n"
            "Нажмите кнопку ниже, чтобы открыть мини-приложение с тестами:",
            reply_markup=keyboard
        )

        logger.info(f"Пользователь {user_id} выбрал мини-апп уровень: {level}, тестов: {len(tests)}")
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка в select_mini_app_level: {e}")
        await message.answer("Произошла ошибка.")


# ======================================================
# WEBAPP RESULT HANDLER
# ======================================================
@dp.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def handle_webapp_result(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)

        user_id = message.from_user.id
        level = data.get("level", "Неизвестно")
        score = data.get("score", 0)
        total = data.get("total", 0)
        coins_earned = data.get("coins_earned", 0)
        if coins_earned > 0:
            await add_coins(user_id, coins_earned)
            
        async with aiosqlite.connect(WORDS_DB) as db:
            await db.execute(
                "INSERT INTO web_results (user_id, level, score, total) VALUES (?, ?, ?, ?)",
                (user_id, level, score, total)
            )
            await db.commit()

        percentage = (score / total * 100) if total > 0 else 0

        if percentage >= 80:
            emoji = "🎉"
            message_text = "Отличный результат!"
        elif percentage >= 60:
            emoji = "👍"
            message_text = "Хороший результат!"
        else:
            emoji = "📚"
            message_text = "Продолжайте учиться!"

        await message.answer(
            f"{emoji} <b>Результат теста</b>\n\n"
            f"🏆 Уровень: {level}\n"
            f"✅ Правильных: {score}/{total}\n"
            f"📊 Процент: {percentage:.1f}%\n\n"
            f"{message_text}\n\n"
            "Результат сохранён в вашу историю.",
            parse_mode="HTML"
        )

        logger.info(f"WebApp результат от {user_id}: {score}/{total} ({level}), {percentage:.1f}%")

    except Exception as e:
        logger.error(f"Ошибка в handle_webapp_result: {e}")
        await message.answer("❌ Ошибка обработки результата теста.")


# ======================================================
# ГРАММАТИЧЕСКИЕ ТЕСТЫ (в боте)
# ======================================================
@dp.message(F.text == "Грамматические тесты (в боте)")
async def grammar_tests_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    async with aiosqlite.connect(TESTS_DB) as db:
        await db.execute("INSERT OR IGNORE INTO user_lives (user_id, lives) VALUES (?, 3)", (user_id,))

    lives = await get_lives(user_id)   # теперь это будет работать с user_live

    kb = [[types.KeyboardButton(text=level)] for level in LEVELS]
    kb.append([types.KeyboardButton(text="Назад")])
    await state.set_state(UserState.grammar_select_level)

    await message.answer(
        f"Выберите уровень грамматики:\n\n❤️ Жизни для грамматических тестов: {lives}",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    )

async def grammar_load_next_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    level = data.get("grammar_level")
    if not level:
        await message.answer("Ошибка: уровень не выбран.")
        await back_to_main(message, state)
        return

    async with aiosqlite.connect(TESTS_DB) as db:
        cur = await db.execute(
            "SELECT id, question, option_a, option_b, option_c, correct, explanation FROM tests WHERE level=? ORDER BY RANDOM() LIMIT 1",
            (level,)
        )
        row = await cur.fetchone()

    if not row:
        await message.answer("Нет тестов для этого уровня.")
        await back_to_main(message, state)
        return

    test_id, q, oa, ob, oc, correct, explanation = row
    await state.update_data(
        current_test=row,
        correct_answer=correct,
        current_explanation=explanation,
        waiting_for_next=False          # флаг, что ещё не отвечено
    )
    await state.set_state(UserState.grammar_waiting_answer)

    options = [("1. " + oa), ("2. " + ob), ("3. " + oc)]
    kb = [[types.KeyboardButton(text=opt)] for opt in options]
    kb.append([types.KeyboardButton(text="Назад")])
    await message.answer(f"📝 {q}", reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

@dp.message(UserState.grammar_select_level, F.text.in_(LEVELS))
async def grammar_start(message: types.Message, state: FSMContext):
    try:
        level = message.text
        await state.update_data(grammar_level=level)
        await grammar_load_next_question(message, state)
    except Exception as e:
        logger.error(f"Ошибка в grammar_start: {e}")
        await message.answer("Произошла ошибка.")

async def grammar_load_next_question(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        level = data.get("grammar_level")
        if not level:
            await message.answer("Ошибка: уровень не выбран.")
            await back_to_main(message, state)
            return

        async with aiosqlite.connect(TESTS_DB) as db:
            cur = await db.execute(
                "SELECT id, question, option_a, option_b, option_c, correct, explanation FROM tests WHERE level=? ORDER BY RANDOM() LIMIT 1",
                (level,)
            )
            row = await cur.fetchone()

        if not row:
            await message.answer("Нет тестов для этого уровня.")
            await back_to_main(message, state)
            return

        test_id, q, oa, ob, oc, correct, explanation = row
        await state.update_data(
            current_test=row,
            correct_answer=correct,
            current_explanation=explanation,
            waiting_for_next=False
        )
        await state.set_state(UserState.grammar_waiting_answer)

        options = [("1. " + oa), ("2. " + ob), ("3. " + oc)]
        kb = [[types.KeyboardButton(text=opt)] for opt in options]
        kb.append([types.KeyboardButton(text="Назад")])
        await message.answer(f"📝 {q}", reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    except Exception as e:
        logger.error(f"Ошибка в grammar_load_next_question: {e}")
        await message.answer("Произошла ошибка при загрузке вопроса.")


@dp.message(UserState.grammar_waiting_answer)
async def grammar_check(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        correct = data.get("correct_answer")
        explanation = data.get("current_explanation", "")
        waiting_for_next = data.get("waiting_for_next", False)
        user_id = message.from_user.id

        # Если уже отвечено и нажата "Далее" – переходим к следующему
        if waiting_for_next:
            await grammar_load_next_question(message, state)
            return

        user_choice = message.text.split('.')[0] if '.' in message.text else ''
        if user_choice == str(correct):
            await add_coins(user_id, 5)
            await message.answer("✅ Правильно! +5 монет!")
        else:
            # Уменьшаем жизнь (теперь вызывается один раз!)
            new_lives = await decrease_life(user_id)
            if new_lives > 0:
                msg = f"❌ Неправильно! Правильный ответ: {correct}\n❤️ Осталось жизней: {new_lives}"
                if explanation:
                    msg += f"\n\n📖 Объяснение: {explanation}"
                await message.answer(msg)
            else:
                # Жизни закончились
                msg = f"❌ Неправильно! Правильный ответ: {correct}\n💀 У вас закончились жизни!"
                if explanation:
                    msg += f"\n\n📖 Объяснение: {explanation}"
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Восстановить жизни (10 монет)", callback_data="restore_grammar_lives")],
                    [InlineKeyboardButton(text="🔁 Выбрать другой уровень", callback_data="choose_other_level")],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                ])
                await message.answer(msg, reply_markup=kb)
                await state.clear()
                return

        # После ответа показываем кнопку "Далее"
        await state.update_data(waiting_for_next=True)
        kb = [[types.KeyboardButton(text="Далее →")], [types.KeyboardButton(text="Назад")]]
        await message.answer("Нажмите «Далее», чтобы продолжить.", reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    except Exception as e:
        logger.error(f"Ошибка в grammar_check: {e}")
        import traceback
        traceback.print_exc()   # <-- добавим полный вывод ошибки в консоль
        await message.answer("Произошла ошибка.")

@dp.message(UserState.grammar_waiting_answer, F.text == "Далее →")
async def grammar_next(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data.get("waiting_for_next"):
        # Передаём управление в grammar_check, который загрузит следующий вопрос
        await grammar_check(message, state)
    else:
        await message.answer("Сначала ответьте на вопрос.")

@dp.callback_query(lambda c: c.data == "restore_grammar_lives")
async def restore_grammar_lives(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if await spend_coins(user_id, 10):
        await increase_life(user_id, amount=3, max_lives=3)
        await callback.message.answer("✅ Жизни восстановлены! Теперь у вас 3 жизни.")
        await grammar_tests_menu(callback.message, state)
    else:
        await callback.message.answer("❌ Недостаточно монет. Зарабатывайте монеты, изучая слова!")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "restore_word_lives")
async def restore_word_lives(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if await spend_coins(user_id, 10):
        await increase_word_life(user_id, amount=3, max_lives=3)
        await callback.message.answer("✅ Жизни восстановлены! Теперь у вас 3 жизни.")
        await learn_words(callback.message, state)
    else:
        await callback.message.answer("❌ Недостаточно монет.")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "restore_word_lives")
async def restore_word_lives(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with aiosqlite.connect(WORDS_DB) as db:
        # Создаём таблицу, если её нет
        await db.execute("""
        CREATE TABLE IF NOT EXISTS word_users (
            user_id INTEGER PRIMARY KEY,
            coins INTEGER DEFAULT 0,
            lives INTEGER DEFAULT 3
        )
        """)
        # Создаём запись, если её нет
        await db.execute("INSERT OR IGNORE INTO word_users (user_id, coins, lives) VALUES (?, 0, 3)", (user_id,))
        await db.commit()

        cursor = await db.execute("SELECT coins FROM word_users WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        if row and row[0] >= 10:
            # Уменьшаем монеты и восстанавливаем жизни
            await db.execute("UPDATE word_users SET coins = coins - 10, lives = 3 WHERE user_id=?", (user_id,))
            await db.commit()
            await callback.message.answer("✅ Жизни восстановлены! Теперь у вас 3 жизни.")
            await learn_words(callback.message, state)  # Возвращаем к изучению слов
        else:
            await callback.message.answer("❌ Недостаточно монет. Зарабатывайте монеты, изучая слова!")
    await callback.answer()    

@dp.callback_query(lambda c: c.data == "choose_other_level")
async def choose_other_level(callback: CallbackQuery, state: FSMContext):
    await grammar_tests_menu(callback.message, state)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "choose_word_level")
async def choose_word_level(callback: CallbackQuery, state: FSMContext):
    await learn_words(callback.message, state)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    await back_to_main(callback.message, state)
    await callback.answer()

# ======================================================
# RUN
# ======================================================
async def main():
    print("=== ЗАПУСК БОТА ===")
    print(f"База слов: {WORDS_DB} - {'существует' if os.path.exists(WORDS_DB) else 'НЕ НАЙДЕНА'}")
    print(f"База тестов: {TESTS_DB} - {'существует' if os.path.exists(TESTS_DB) else 'НЕ НАЙДЕНА'}")

    if os.path.exists(WORDS_DB):
        import sqlite3
        conn = sqlite3.connect(WORDS_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT level, COUNT(*) FROM words GROUP BY level")
        print("Слова в базе:")
        words_found = False
        for level, count in cursor.fetchall():
            print(f"  {level}: {count} слов")
            words_found = True
        if not words_found:
            print("  ❌ БАЗА ПУСТА! Запустите: python generate_words.py")
        conn.close()

    await init_databases()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
