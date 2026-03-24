import sqlite3

def check_db(db_file):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
    exists = c.fetchone()
    if exists:
        c.execute("SELECT COUNT(*) FROM words")
        count = c.fetchone()[0]
        print(f"{db_file}: таблица 'words' существует, записей: {count}")
    else:
        print(f"{db_file}: таблица 'words' отсутствует")
    conn.close()

check_db("bot.db")
check_db("db.sqlite3")