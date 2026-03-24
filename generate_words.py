import aiosqlite
import asyncio

# База из популярных английских слов с разными уровнями сложности
WORD_DATABASE = [
    # Начальный уровень
    {"word": "hello", "transcription": "/həˈləʊ/", "translation": "привет", "example_english": "Hello, how are you?",
     "example_russian": "Привет, как дела?", "level": "Начальный"},
    {"word": "goodbye", "transcription": "/ɡʊdˈbaɪ/", "translation": "до свидания",
     "example_english": "She said goodbye and left.", "example_russian": "Она сказала до свидания и ушла.",
     "level": "Начальный"},
    {"word": "thank you", "transcription": "/ˈθæŋk juː/", "translation": "спасибо",
     "example_english": "Thank you for your help.", "example_russian": "Спасибо за вашу помощь.", "level": "Начальный"},
    {"word": "please", "transcription": "/pliːz/", "translation": "пожалуйста", "example_english": "Please come in.",
     "example_russian": "Пожалуйста, заходи.", "level": "Начальный"},
    {"word": "yes", "transcription": "/jes/", "translation": "да", "example_english": "Yes, I understand.",
     "example_russian": "Да, я понимаю.", "level": "Начальный"},
    {"word": "no", "transcription": "/nəʊ/", "translation": "нет", "example_english": "No, thank you.",
     "example_russian": "Нет, спасибо.", "level": "Начальный"},
    {"word": "water", "transcription": "/ˈwɔːtər/", "translation": "вода",
     "example_english": "I drink water every day.", "example_russian": "Я пью воду каждый день.", "level": "Начальный"},
    {"word": "food", "transcription": "/fuːd/", "translation": "еда", "example_english": "The food is delicious.",
     "example_russian": "Еда очень вкусная.", "level": "Начальный"},
    {"word": "house", "transcription": "/haʊs/", "translation": "дом", "example_english": "They bought a new house.",
     "example_russian": "Они купили новый дом.", "level": "Начальный"},
    {"word": "family", "transcription": "/ˈfæməli/", "translation": "семья",
     "example_english": "My family lives in Moscow.", "example_russian": "Моя семья живет в Москве.",
     "level": "Начальный"},

    # Средний уровень
    {"word": "opportunity", "transcription": "/ˌɒpəˈtjuːnəti/", "translation": "возможность",
     "example_english": "This is a great opportunity for you.", "example_russian": "Это отличная возможность для тебя.",
     "level": "Средний"},
    {"word": "development", "transcription": "/dɪˈveləpmənt/", "translation": "развитие",
     "example_english": "The development of technology is rapid.",
     "example_russian": "Развитие технологий происходит быстро.", "level": "Средний"},
    {"word": "environment", "transcription": "/ɪnˈvaɪrənmənt/", "translation": "окружающая среда",
     "example_english": "We must protect the environment.", "example_russian": "Мы должны защищать окружающую среду.",
     "level": "Средний"},
    {"word": "government", "transcription": "/ˈɡʌvənmənt/", "translation": "правительство",
     "example_english": "The government announced new policies.",
     "example_russian": "Правительство объявило о новых политиках.", "level": "Средний"},
    {"word": "education", "transcription": "/ˌedʒʊˈkeɪʃən/", "translation": "образование",
     "example_english": "Education is important for success.", "example_russian": "Образование важно для успеха.",
     "level": "Средний"},
    {"word": "knowledge", "transcription": "/ˈnɒlɪdʒ/", "translation": "знание",
     "example_english": "He has extensive knowledge of history.",
     "example_russian": "У него обширные знания по истории.", "level": "Средний"},
    {"word": "experience", "transcription": "/ɪkˈspɪəriəns/", "translation": "опыт",
     "example_english": "She has years of experience in marketing.",
     "example_russian": "У нее годы опыта в маркетинге.", "level": "Средний"},
    {"word": "relationship", "transcription": "/rɪˈleɪʃənʃɪp/", "translation": "отношения",
     "example_english": "They have a good working relationship.", "example_russian": "У них хорошие рабочие отношения.",
     "level": "Средний"},
    {"word": "technology", "transcription": "/tekˈnɒlədʒi/", "translation": "технология",
     "example_english": "Modern technology changes quickly.",
     "example_russian": "Современные технологии быстро меняются.", "level": "Средний"},
    {"word": "information", "transcription": "/ˌɪnfəˈmeɪʃən/", "translation": "информация",
     "example_english": "We need more information to decide.",
     "example_russian": "Нам нужно больше информации для решения.", "level": "Средний"},

    # Продвинутый уровень
    {"word": "comprehensive", "transcription": "/ˌkɒmprɪˈhensɪv/", "translation": "всеобъемлющий",
     "example_english": "The report provides a comprehensive analysis.",
     "example_russian": "Отчет предоставляет всеобъемлющий анализ.", "level": "Продвинутый"},
    {"word": "sophisticated", "transcription": "/səˈfɪstɪkeɪtɪd/", "translation": "сложный, изощренный",
     "example_english": "They use sophisticated equipment.", "example_russian": "Они используют сложное оборудование.",
     "level": "Продвинутый"},
    {"word": "ubiquitous", "transcription": "/juːˈbɪkwɪtəs/", "translation": "вездесущий",
     "example_english": "Smartphones have become ubiquitous.", "example_russian": "Смартфоны стали вездесущими.",
     "level": "Продвинутый"},
    {"word": "meticulous", "transcription": "/məˈtɪkjələs/", "translation": "педантичный",
     "example_english": "She is meticulous in her work.", "example_russian": "Она педантична в своей работе.",
     "level": "Продвинутый"},
    {"word": "ambiguous", "transcription": "/æmˈbɪɡjuəs/", "translation": "двусмысленный",
     "example_english": "His answer was ambiguous.", "example_russian": "Его ответ был двусмысленным.",
     "level": "Продвинутый"},
    {"word": "phenomenon", "transcription": "/fəˈnɒmɪnən/", "translation": "феномен",
     "example_english": "This natural phenomenon is rare.", "example_russian": "Этот природный феномен редок.",
     "level": "Продвинутый"}
]


async def init_words_table():
    """Создание таблицы слов если она не существует"""
    async with aiosqlite.connect("db.sqlite3") as db:
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
        print("Таблица 'words' создана или уже существует")


async def init_words_table():
    async with aiosqlite.connect("db.sqlite3") as db:
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
        print("Таблица 'words' готова")

async def populate_database():
    await init_words_table()
    async with aiosqlite.connect("db.sqlite3") as db:
        await db.execute("DELETE FROM words")  # очистка
        for w in WORD_DATABASE:
            await db.execute('''
                INSERT INTO words (word, transcription, translation, example_english, example_russian, level)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (w['word'], w['transcription'], w['translation'],
                  w['example_english'], w['example_russian'], w['level']))
        await db.commit()
        print(f"✅ Добавлено {len(WORD_DATABASE)} слов")

async def check_database():
    async with aiosqlite.connect("db.sqlite3") as db:
        cursor = await db.execute("SELECT COUNT(*) FROM words")
        count = await cursor.fetchone()
        print(f"📊 Всего слов: {count[0]}")
        cursor = await db.execute("SELECT word, level FROM words LIMIT 5")
        rows = await cursor.fetchall()
        print("📝 Примеры:")
        for word, level in rows:
            print(f"   {word} ({level})")

if __name__ == "__main__":
    print("🔄 Заполнение базы...")
    asyncio.run(populate_database())
    asyncio.run(check_database())
    print("✅ Готово")