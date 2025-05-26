import sqlite3
import asyncio
from datetime import datetime, timedelta
def init_db():
    conn = sqlite3.connect("freelance_bot.db")
    cur = conn.cursor()

    # Users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE,
            username TEXT,
            created_at TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0
        )
    ''')

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            ad_text TEXT,
            contact TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS keywords (
            user_id INTEGER,
            keyword TEXT
        )
    """)

    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER PRIMARY KEY,
            subscribed_until TEXT
        )
    """)

    conn.commit()
    conn.close()




def is_user_subscribed(user_id: int) -> bool:
    conn = sqlite3.connect("freelance_bot.db")
    cur = conn.cursor()
    cur.execute("SELECT subscribed_until FROM subscriptions WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    return datetime.fromisoformat(row[0]) > datetime.now()

def activate_subscription(user_id: int):
    subscribed_until = datetime.now() + timedelta(days=30)
    conn = sqlite3.connect("freelance_bot.db")
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO subscriptions (user_id, subscribed_until) VALUES (?, ?)", (user_id, subscribed_until.isoformat()))
    conn.commit()
    conn.close()





def save_ad(user_id: int, role: str, ad_text: str, contact: str):
    conn = sqlite3.connect("freelance_bot.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO ads (user_id, role, ad_text, contact) VALUES (?, ?, ?, ?)", (user_id, role, ad_text, contact))
    conn.commit()
    conn.close()

def get_user_ads(user_id: int) -> list:
    conn = sqlite3.connect("freelance_bot.db")
    cur = conn.cursor()
    cur.execute("SELECT role, ad_text, contact, created_at FROM ads WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    result = cur.fetchall()
    conn.close()
    return result


def save_keywords(user_id: int, keywords: list[str]):
    conn = sqlite3.connect("freelance_bot.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM keywords WHERE user_id = ?", (user_id,))
    for kw in keywords:
        cur.execute("INSERT INTO keywords (user_id, keyword) VALUES (?, ?)", (user_id, kw.strip().lower()))
    conn.commit()
    conn.close()

def get_all_keyword_users() -> dict:
    conn = sqlite3.connect("freelance_bot.db")
    cur = conn.cursor()
    cur.execute("SELECT user_id, keyword FROM keywords")
    rows = cur.fetchall()
    conn.close()

    user_keywords = {}
    for user_id, keyword in rows:
        user_keywords.setdefault(user_id, set()).add(keyword)
    return user_keywords




def notify_vip_users(bot, message_text: str):
    from db import get_all_vip_users

    vip_users = get_all_vip_users()
    for user_id, keywords in vip_users:
        if not keywords:
            continue
        for word in keywords.split(","):
            if word.strip() and word.strip().lower() in message_text.lower():
                asyncio.create_task(bot.send_message(chat_id=user_id, text=message_text))
                break  # فقط یک بار به هر کاربر بفرسته



def save_user(telegram_id: int, username: str):
    import datetime
    conn = sqlite3.connect("freelance_bot.db")
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO users (telegram_id, username, created_at) VALUES (?, ?, ?)",
        (telegram_id, username, datetime.datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
