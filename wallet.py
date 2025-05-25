# freelance_bot/wallet.py
import sqlite3


def create_wallet_if_not_exists(user_id: int):
    conn = sqlite3.connect("freelance_bot.db")
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO wallets (user_id, balance) VALUES (?, 0)", (user_id,))
    conn.commit()
    conn.close()


def get_wallet_balance(user_id: int) -> int:
    conn = sqlite3.connect("freelance_bot.db")
    cur = conn.cursor()
    cur.execute("SELECT balance FROM wallets WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else 0


def increase_wallet(user_id: int, amount: int):
    create_wallet_if_not_exists(user_id)
    conn = sqlite3.connect("freelance_bot.db")
    cur = conn.cursor()
    cur.execute("UPDATE wallets SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()


def decrease_wallet(user_id: int, amount: int) -> bool:
    balance = get_wallet_balance(user_id)
    if balance >= amount:
        conn = sqlite3.connect("freelance_bot.db")
        cur = conn.cursor()
        cur.execute("UPDATE wallets SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()
        return True
    return False
