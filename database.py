import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "quiz.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def add_question(question, option_a, option_b, option_c, option_d, correct):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (question, option_a, option_b, option_c, option_d, correct),
    )
    conn.commit()
    conn.close()


def get_all_questions():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, question, option_a, option_b, option_c, option_d, correct FROM questions")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_questions_page(offset: int, limit: int = 50):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, question, option_a, option_b, option_c, option_d, correct FROM questions LIMIT ? OFFSET ?",
        (limit, offset),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_question_count():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM questions")
    count = cur.fetchone()[0]
    conn.close()
    return count


def clear_all_questions():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM questions")
    conn.commit()
    conn.close()


def delete_question(question_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM questions WHERE id = ?", (question_id,))
    conn.commit()
    conn.close()
