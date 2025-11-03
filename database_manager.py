# database_manager.py

import sqlite3
import os
from typing import List

DB_FILE = "subscriptions.db"

def get_db_connection():
    """Tạo kết nối đến database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Khởi tạo bảng trong database nếu chưa tồn tại."""
    if os.path.exists(DB_FILE):
        print("Database đã tồn tại.")
        return
        
    print("Đang khởi tạo database...")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        ticker TEXT NOT NULL,
        subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(email, ticker)
    );
    """)
    conn.commit()
    conn.close()
    print("Khởi tạo database thành công.")

def add_subscription(email: str, ticker: str):
    """Thêm một lượt đăng ký mới vào database."""
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO subscriptions (email, ticker) VALUES (?, ?)", (email, ticker.upper()))
        conn.commit()
        print(f"Đã thêm đăng ký: {email} cho mã {ticker.upper()}")
    except sqlite3.IntegrityError:
        print(f"Lỗi: {email} đã đăng ký nhận tin cho mã {ticker.upper()} từ trước.")
    finally:
        conn.close()

def get_unique_tickers() -> List[str]:
    """Lấy danh sách duy nhất các mã cổ phiếu đã được đăng ký."""
    conn = get_db_connection()
    tickers = conn.execute("SELECT DISTINCT ticker FROM subscriptions ORDER BY ticker").fetchall()
    conn.close()
    return [row['ticker'] for row in tickers]

def get_emails_for_ticker(ticker: str) -> List[str]:
    """Lấy danh sách email đã đăng ký cho một mã cổ phiếu cụ thể."""
    conn = get_db_connection()
    emails = conn.execute("SELECT email FROM subscriptions WHERE ticker = ?", (ticker.upper(),)).fetchall()
    conn.close()
    return [row['email'] for row in emails]

def populate_dummy_data():
    """Thêm một vài dữ liệu mẫu để thử nghiệm."""
    print("Đang thêm dữ liệu mẫu...")
    init_db()
    add_subscription("nguyentrongtin18042004@gmail.com", "FPT")
    # add_subscription("user3@example.com", "VCB")
    print("Thêm dữ liệu mẫu hoàn tất.")

if __name__ == '__main__':
    populate_dummy_data()