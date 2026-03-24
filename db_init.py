# db_init.py
import aiosqlite
import asyncio

DB = "bot.db"

# Все тесты: (level, question, option_a, option_b, option_c, correct)
tests = [
    # Начальный
    ("Начальный","Choose the correct form: He always _____ up early.","wake","wakes","waking","B"),
    ("Начальный","We _____ lunch at school every day.","eat","eats","eating","A"),
    ("Начальный","She _____ a picture now. (present continuous)","is drawing","draws","drawing","A"),
    ("Начальный","I bought _____ umbrella yesterday.","an","a","the","A"),
    ("Начальный","One tomato, two _____.","tomatoes","tomatos","tomatoes","A"),
    ("Начальный","They usually _____ in the park on Sundays.","play","plays","playing","A"),
    ("Начальный","She always _____ her homework on time.","does","do","doing","A"),
    ("Начальный","I _____ TV now. (present continuous)","am watching","watch","watches","A"),
    ("Начальный","He wants _____ orange from the basket.","an","a","the","A"),
    ("Начальный","One baby, three _____.","babies","baby","babys","A"),
    ("Начальный","She _____ to school every day.","go","goes","going","B"),
    ("Начальный","I _____ coffee every morning.","drinks","drink","am drinking","B"),
    ("Начальный","He _____ his homework now. (present continuous)","do","does","is doing","C"),
    ("Начальный","_____ apple a day keeps the doctor away.","An","A","The","A"),
    ("Начальный","One cat, two _____.","cats","cat","cates","A"),
    ("Начальный","They _____ football on Sundays.","play","plays","playing","A"),
    ("Начальный","She _____ very fast.","run","runs","running","B"),
    ("Начальный","I _____ English now. (present continuous)","am learning","learn","learning","A"),
    ("Начальный","I saw _____ cat in the garden.","a","an","the","A"),
    ("Начальный","One dog, three _____.","dogs","dog","doges","A"),
    ("Начальный","He _____ TV every evening.","watch","watches","watching","B"),
    ("Начальный","We _____ to music every day.","listen","listens","listening","A"),
    ("Начальный","She _____ a book now. (present continuous)","reads","is reading","reading","B"),
    ("Начальный","I want _____ orange.","an","a","the","A"),
    ("Начальный","One mouse, two _____.","mouses","mice","mouse","B"),
    ("Начальный","I _____ breakfast at 7 a.m.","have","has","having","A"),
    ("Начальный","She _____ very happy today.","is","are","am","A"),
    ("Начальный","They _____ soccer now. (present continuous)","play","are playing","plays","B"),
    ("Начальный","_____ sun is shining.","The","A","An","A"),
    ("Начальный","One child, two _____.","childs","children","childes","B"),

    # Средний
    ("Средний","She _____ just completed her course.","has","have","had","A"),
    ("Средний","I _____ at this company since 2018. (Present Perfect)","have worked","worked","am working","A"),
    ("Средний","If I _____ harder, I would have passed the exam.","had studied","studied","study","A"),
    ("Средний","Reported speech: 'I must leave now' -> He said he _____ leave.","had to","must","should","A"),
    ("Средний","They _____ for two hours when I arrived.","had been studying","studied","were studying","A"),
    ("Средний","By the time I got there, she _____ already left.","had","has","have","A"),
    ("Средний","If he _____ more careful, he wouldn't have lost his wallet.","had been","was","is","A"),
    ("Средний","Reported speech: 'I can run fast' -> He said he _____ run fast.","could","can","was able to","A"),
    ("Средний","I _____ here since morning.","have been waiting","am waiting","waited","A"),
    ("Средний","She _____ homework when I called. (Past Continuous)","was doing","did","has done","A"),
    ("Средний","I _____ here for two hours.","have been","am","was","A"),
    ("Средний","He said 'I am tired' -> He said that he _____ tired.","was","is","has been","A"),
    ("Средний","By next year, she _____ in London for five years.","will live","will have lived","lives","B"),
    ("Средний","I _____ my homework before he came.","had finished","have finished","finished","A"),
    ("Средний","She said 'I can swim' -> She said that she _____ swim.","could","can","was able to","A"),
    ("Средний","If I _____ you, I would apologize.","am","were","was","B"),
    ("Средний","She _____ already finished her work.","has","have","had","A"),
    ("Средний","They _____ the project for three weeks. (Present Perfect Continuous)","have been doing","are doing","did","A"),
    ("Средний","He said he _____ already seen the movie.","had","has","have","A"),
    ("Средний","'I will help you' -> He said he _____ help me.","would","will","can","A"),
    ("Средний","She _____ to Paris many times.","has been","was","went","A"),
    ("Средний","If it _____ tomorrow, we will stay home.","rains","rain","rained","A"),
    ("Средний","By the time we arrived, they _____ already left.","had","have","has","A"),
    ("Средний","'I may come' -> He said he _____ come.","might","may","can","A"),
    ("Средний","She _____ her keys if she had looked in the bag.","would find","would have found","finds","B"),
    ("Средний","I _____ since morning.","have been working","am working","worked","A"),
    ("Средний","'I had finished my homework' -> He said he _____ finished his homework.","had","has","have","A"),
    ("Средний","I wish I _____ more time yesterday.","have","had","has","B"),
    ("Средний","She _____ in the garden when I saw her. (Past Continuous)","was working","worked","works","A"),
    ("Средний","I _____ this book before.","have read","readed","read","A"),
    ("Средний","If I _____ rich, I would buy a house.","am","were","was","B"),
    ("Средний","'I must go now' -> He said he _____ go then.","had to","must","should","A"),
    ("Средний","They _____ dinner when I called.","were having","had","have had","A"),
    ("Средний","I _____ to London many times before.","have been","was","had been","A"),
    ("Средний","If it _____ yesterday, we would have stayed home.","rained","rains","rain","A"),
    ("Средний","He _____ here since 2010.","has been","is","was","A"),
    ("Средний","'I can swim fast' -> He said he _____ swim fast.","could","can","was able to","A"),
    ("Средний","If you _____ earlier, you wouldn't have missed the train.","had left","leave","left","A"),
    ("Средний","She _____ all morning when I visited. (Past Continuous)","was cleaning","cleaned","is cleaning","A"),

    # Продвинутый
    ("Продвинутый","It was John _____ broke the vase.","who","which","that","A"),
    ("Продвинутый","Rarely _____ such a mistake.","had I seen","I had seen","did I see","A"),
    ("Продвинутый","Not only _____ the project, but also managed the team.","did she complete","she completed","completed she","A"),
    ("Продвинутый","It is the manager _____ decided the new policy.","who","which","that","A"),
    ("Продвинутый","Little _____ he know about the consequences.","did","does","was","A"),
    ("Продвинутый","It was the book _____ won the award.","which","who","that","A"),
    ("Продвинутый","Seldom _____ such a beautiful view.","have I seen","I have seen","did I see","A"),
    ("Продвинутый","Only after the meeting _____ the report.","did they submit","they submitted","submitted they","A"),
    ("Продвинутый","It was the engineer _____ solved the problem.","who","which","that","A"),
    ("Продвинутый","Not until yesterday _____ the truth.","did I learn","I learned","learned I","A"),
    ("Продвинутый","It was the proposal _____ changed the company's strategy.","that","who","which","A"),
    ("Продвинутый","Rarely _____ he seen such dedication.","had","has","did","A"),
    ("Продвинутый","Only by working hard _____ success.","can you achieve","you can achieve","achieve you","A"),
    ("Продвинутый","It was the student _____ got the highest mark.","who","which","that","A"),
    ("Продвинутый","Hardly _____ the meeting started when the fire alarm rang.","had","has","did","A"),
    ("Продвинутый","It was the team _____ won the championship.","that","who","which","A"),
    ("Продвинутый","No sooner _____ the match started than it began to rain.","had","has","did","A"),
    ("Продвинутый","Only in this way _____ the problem solved.","can be","is","was","A"),
    ("Продвинутый","It was the innovation _____ revolutionized the industry.","that","who","which","A"),
    ("Продвинутый","Scarcely _____ the lecture begun when the fire alarm went off.","had","has","did","A"),
    ("Продвинутый","It was the scientist _____ discovered the cure.","who","which","that","A"),
    ("Продвинутый","Not only _____ she intelligent, but also hardworking.","is","was","did","A"),
    ("Продвинутый","Only then _____ the solution become clear.","did","does","was","A"),
    ("Продвинутый","It was the decision _____ changed everything.","that","who","which","A"),
    ("Продвинутый","Rarely _____ she encountered such difficulties.","has","did","had","B"),
    ("Продвинутый","It was the manager _____ approved the budget.","who","which","that","A"),
    ("Продвинутый","Hardly _____ she left the office when it started raining.","had","has","did","A")
]

async def init_db():
    async with aiosqlite.connect(DB) as db:
        # Таблица тестов
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            question TEXT,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            correct CHAR(1)
        );
        """)

        # Очистка старых тестов
        await db.execute("DELETE FROM tests;")
        # Вставка тестов
        for t in tests:
            await db.execute(
                "INSERT INTO tests (level, question, option_a, option_b, option_c, correct) VALUES (?, ?, ?, ?, ?, ?)",
                t
            )

        # Таблица пользователей с жизнями
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            coins INTEGER DEFAULT 0,
            correct_answers INTEGER DEFAULT 0,
            lives INTEGER DEFAULT 3,
            streak INTEGER DEFAULT 0
        );
        """)

        await db.commit()
    print("DB initialized: tests =", len(tests), "| users table ready")

# Функции для работы с жизнями (можно импортировать в bot.py)
async def get_lives(user_id: int):
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT lives FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def decrease_life(user_id: int):
    async with aiosqlite.connect(DB) as db:
        lives = await get_lives(user_id)
        if lives is None or lives <= 0:
            return False
        await db.execute("UPDATE users SET lives = lives - 1 WHERE user_id = ?", (user_id,))
        await db.commit()
        return True

async def increase_life(user_id: int, amount: int = 1, max_lives: int = 3):
    async with aiosqlite.connect(DB) as db:
        lives = await get_lives(user_id)
        if lives is None:
            return False
        new_lives = min(lives + amount, max_lives)
        await db.execute("UPDATE users SET lives = ? WHERE user_id = ?", (new_lives, user_id))
        await db.commit()
        return new_lives

if __name__ == "__main__":
    asyncio.run(init_db())