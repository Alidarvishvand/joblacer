import sqlite3

def init_db():
    conn = sqlite3.connect("freelance_bot.db")
    cur = conn.cursor()

    # Users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE,
            username TEXT,
            role TEXT CHECK(role IN ('employer', 'freelancer')),
            skills TEXT,
            created_at TEXT
        )
    ''')

    # Projects table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY,
            employer_id INTEGER,
            title TEXT,
            description TEXT,
            budget INTEGER,
            deadline TEXT,
            created_at TEXT,
            FOREIGN KEY (employer_id) REFERENCES users(id)
        )
    ''')

    
    cur.execute('''
    CREATE TABLE IF NOT EXISTS wallets (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )
''')
    
    # Proposals table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY,
            project_id INTEGER,
            freelancer_id INTEGER,
            proposal_text TEXT,
            proposed_budget INTEGER,
            created_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (freelancer_id) REFERENCES users(id)
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
