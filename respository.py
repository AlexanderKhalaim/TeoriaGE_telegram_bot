import psycopg2
from psycopg2 import sql


def connection():
    return psycopg2.connect(
        dbname="teoria_ge",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432"
    )


def create_users(db):
    cur = db.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id SERIAL PRIMARY KEY,
        tg_user_id INTEGER UNIQUE,
        username VARCHAR(128),
        current_round_id INTEGER
    )
    """)
    db.commit()


def create_questions(db):
    cur = db.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        question_id SERIAL PRIMARY KEY,
        category VARCHAR(16),
        text TEXT,
        description TEXT
    )
    """)
    db.commit()


def create_answers(db):
    cur = db.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS answers (
        answer_id SERIAL PRIMARY KEY,
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
        stat_id SERIAL PRIMARY KEY,
        tg_user_id INTEGER,
        round_type VARCHAR(128),
        category VARCHAR(16),
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
        mistakes_question_id SERIAL PRIMARY KEY,
        tg_user_id INTEGER,
        question_id INTEGER,
        FOREIGN KEY (tg_user_id) REFERENCES users(tg_user_id),
        FOREIGN KEY (question_id) REFERENCES questions(question_id)
    )
    """)
    db.commit()



def add_foreign_key_users(db):
    cur = db.cursor()
    cur.execute("""
    ALTER TABLE users
    ADD CONSTRAINT fk_current_round
    FOREIGN KEY (current_round_id) REFERENCES stats(stat_id)
    """)
    db.commit()


database = connection()
create_users(database)
create_questions(database)
create_answers(database)
create_stats(database)
create_mistake_questions(database)
add_foreign_key_users(database)
database.close()
