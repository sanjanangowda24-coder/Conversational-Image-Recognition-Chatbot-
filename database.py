import sqlite3

DB_FILE = "saanra.db"

# -------------------------------
# Initialize Database
# -------------------------------
def create_tables():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        sender TEXT NOT NULL,
        message TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
    )
    """)

    conn.commit()
    conn.close()

# -------------------------------
# User Functions
# -------------------------------
def add_user(username, password):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def validate_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# -------------------------------
# Chat Session Functions
# -------------------------------
def create_session(user_id, session_name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_sessions (user_id, session_name) VALUES (?, ?)", (user_id, session_name))
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id

def save_message(session_id, sender, message):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_messages (session_id, sender, message) VALUES (?, ?, ?)", (session_id, sender, message))
    conn.commit()
    conn.close()

def get_user_sessions(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, session_name FROM chat_sessions WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    sessions = cursor.fetchall()
    conn.close()
    return sessions

def get_chat_messages(session_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT sender, message FROM chat_messages WHERE session_id=? ORDER BY timestamp ASC", (session_id,))
    messages = cursor.fetchall()
    conn.close()
    return messages
# -------------------------------
# Rename Chat Session
# -------------------------------
def rename_session(session_id, new_name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE chat_sessions SET session_name=? WHERE id=?", (new_name, session_id))
    conn.commit()
    conn.close()

# -------------------------------
# Delete Chat Session
# -------------------------------
def delete_session(session_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages WHERE session_id=?", (session_id,))
    cursor.execute("DELETE FROM chat_sessions WHERE id=?", (session_id,))
    conn.commit()
    conn.close()

# -------------------------------
# Run once to create tables
if __name__ == "__main__":
    create_tables()
    print("✅ Database tables created successfully!")
