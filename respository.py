import sqlite3


def create_users(db):
    cur = db.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_user_id INTEGER UNIQUE,
        username TEXT,
        current_round_id INTEGER,
        FOREIGN KEY (current_round_id) REFERENCES stats(stat_id)
    )
    """)
    db.commit()


def create_questions(db):
    cur = db.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        question_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        text TEXT,
        description TEXT
    )
    """)
    db.commit()


def create_answers(db):
    cur = db.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS answers (
        answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        text TEXT,
        is_right INTEGER,
        FOREIGN KEY (question_id) REFERENCES questions(question_id)
    )
    """)
    db.commit()


def create_stats(db):
    cur = db.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stats (
        stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_user_id INTEGER,
        round_type TEXT,
        category TEXT,
        round_num INTEGER,
        correct_cnt INTEGER,
        mistakes_cnt INTEGER,
        list_of_question_ids TEXT,
        FOREIGN KEY (tg_user_id) REFERENCES users(tg_user_id)
    )
    """)
    db.commit()


def create_mistake_questions(db):
    cur = db.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS mistake_questions (
        mistakes_question_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_user_id INTEGER,
        question_id INTEGER,
        FOREIGN KEY (tg_user_id) REFERENCES users(tg_user_id),
        FOREIGN KEY (question_id) REFERENCES questions(question_id)
    )
    """)
    db.commit()


database = sqlite3.connect('teoria.db')
create_users(database)
create_questions(database)
create_answers(database)
create_stats(database)
create_mistake_questions(database)
database.close()
