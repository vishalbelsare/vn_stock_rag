# database_manager.py
import sqlite3
import json
from datetime import datetime

DB_NAME = "finai.db"

def init_db():
    """Khởi tạo bảng nếu chưa có"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT,
                    current_ticker TEXT,
                    context_report TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )''')
    
    conn.commit()
    conn.close()

def add_user(email, ticker):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO users (email, ticker) VALUES (?, ?)", (email, ticker.upper()))
    conn.commit()
    conn.close()
    
def get_unique_tickers():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT ticker FROM users")
    tickers = [row[0] for row in c.fetchall()]
    conn.close()
    return tickers

def get_emails_for_ticker(ticker):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT email FROM users WHERE ticker = ?", (ticker,))
    emails = [row[0] for row in c.fetchall()]
    conn.close()
    return emails

# --- QUẢN LÝ SESSION & CHAT ---
def create_session(session_id, title="Đoạn chat mới"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Kiểm tra tồn tại
    c.execute("SELECT session_id FROM sessions WHERE session_id = ?", (session_id,))
    if not c.fetchone():
        c.execute("INSERT INTO sessions (session_id, title) VALUES (?, ?)", (session_id, title))
        conn.commit()
    conn.close()

def update_session_metadata(session_id, current_ticker=None, context_report=None, title=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if current_ticker:
        c.execute("UPDATE sessions SET current_ticker = ? WHERE session_id = ?", (current_ticker, session_id))
    if context_report:
        c.execute("UPDATE sessions SET context_report = ? WHERE session_id = ?", (context_report, session_id))
    if title:
        c.execute("UPDATE sessions SET title = ? WHERE session_id = ?", (title, session_id))
    
    c.execute("UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

def get_session_data(session_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def add_message(session_id, role, content):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)", 
              (session_id, role, content))
    conn.commit()
    conn.close()

def get_messages(session_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_sessions_preview():
    """Lấy danh sách session để hiển thị Sidebar"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT session_id, title, created_at FROM sessions ORDER BY updated_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

init_db()