import sqlite3
import os
import json
from datetime import datetime
from config import DB_PATH, BASE_DIR

DB_FULL_PATH = os.path.join(BASE_DIR, DB_PATH)


def get_connection():
    os.makedirs(os.path.dirname(DB_FULL_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_FULL_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            action_id INTEGER NOT NULL,
            context_vector TEXT NOT NULL,
            reward REAL,
            reading_speed_wpm REAL,
            regression_count INTEGER,
            explicit_feedback REAL,
            article_url TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id TEXT PRIMARY KEY,
            session_count INTEGER DEFAULT 0,
            avg_reward REAL DEFAULT 0.0,
            last_action_id INTEGER DEFAULT 0,
            preferred_config TEXT DEFAULT '{}'
        )
    """)
    conn.commit()
    conn.close()


def save_session(user_id, action_id, context_vector, reward,
                 reading_speed_wpm, regression_count, explicit_feedback,
                 article_url=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO sessions
        (user_id, timestamp, action_id, context_vector, reward,
         reading_speed_wpm, regression_count, explicit_feedback, article_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        datetime.utcnow().isoformat(),
        action_id,
        json.dumps(context_vector),
        reward,
        reading_speed_wpm,
        regression_count,
        explicit_feedback,
        article_url,
    ))
    conn.commit()

    c.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
    profile = c.fetchone()
    if profile:
        new_count = profile["session_count"] + 1
        new_avg = (profile["avg_reward"] * profile["session_count"] + reward) / new_count
        c.execute("""
            UPDATE user_profiles
            SET session_count = ?, avg_reward = ?, last_action_id = ?
            WHERE user_id = ?
        """, (new_count, round(new_avg, 4), action_id, user_id))
    else:
        c.execute("""
            INSERT INTO user_profiles (user_id, session_count, avg_reward, last_action_id)
            VALUES (?, 1, ?, ?)
        """, (user_id, reward, action_id))
    conn.commit()
    conn.close()


def get_user_session_count(user_id: str) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT session_count FROM user_profiles WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row["session_count"] if row else 0


def get_all_sessions(user_id: str) -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM sessions WHERE user_id = ? ORDER BY timestamp", (user_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows