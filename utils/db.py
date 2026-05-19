import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'career_data.db')

def get_conn():
    # Ensure database directory exists
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
        except (OSError, PermissionError):
            # If we can't create the directory, use an in-memory database
            return sqlite3.connect(':memory:', check_same_thread=False)
    
    try:
        return sqlite3.connect(DB_PATH, check_same_thread=False)
    except (sqlite3.OperationalError, PermissionError):
        # Fallback to in-memory database if file creation fails
        return sqlite3.connect(':memory:', check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS resume_analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        score INTEGER, verdict TEXT, summary TEXT,
        matched_skills TEXT, missing_skills TEXT,
        strengths TEXT, weaknesses TEXT,
        rewrite_tips TEXT, interview_questions TEXT,
        model_used TEXT, full_result TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS skill_trends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        skills_json TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS interview_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        role TEXT, company TEXT,
        questions_json TEXT, practiced INTEGER DEFAULT 0
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS cover_letters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        company TEXT, role TEXT,
        formal TEXT, conversational TEXT, bold TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS daily_briefings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT UNIQUE,
        briefing TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS github_analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        username TEXT, score INTEGER,
        full_result TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS roadmaps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        target_roles TEXT,
        roadmap_json TEXT,
        completed_skills TEXT DEFAULT '[]'
    )""")

    conn.commit()
    conn.close()
