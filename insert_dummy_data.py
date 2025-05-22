import sqlite3
import hashlib
import datetime
import random

DB_PATH = 'aidiary.db'
DUMMY_USERNAME = 'testuser'
DUMMY_PASSWORD = 'test123'
DUMMY_EMAIL = 'testuser@example.com'

MOODS = ['happy', 'sad', 'neutral', 'angry', 'excited', 'anxious', 'calm']


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def ensure_chat_sessions_table(conn):
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    conn.commit()

def main():
    conn = sqlite3.connect(DB_PATH)
    ensure_chat_sessions_table(conn)
    c = conn.cursor()

    # Check if user exists
    c.execute('SELECT id FROM users WHERE username = ?', (DUMMY_USERNAME,))
    user = c.fetchone()
    if user:
        user_id = user[0]
        print(f"User '{DUMMY_USERNAME}' already exists with id {user_id}.")
    else:
        # Insert dummy user
        hashed_pw = hash_password(DUMMY_PASSWORD)
        c.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                  (DUMMY_USERNAME, hashed_pw, DUMMY_EMAIL))
        user_id = c.lastrowid
        print(f"Inserted dummy user '{DUMMY_USERNAME}' with id {user_id}.")

    # Insert 30 days of mood entries
    today = datetime.date.today()
    for i in range(30):
        entry_date = today - datetime.timedelta(days=i)
        mood = random.choice(MOODS)
        note = f"Dummy note for {entry_date} feeling {mood}."
        # Check if entry already exists
        c.execute('SELECT id FROM mood_entries WHERE user_id = ? AND date = ?', (user_id, entry_date))
        if not c.fetchone():
            c.execute('INSERT INTO mood_entries (user_id, date, mood, note) VALUES (?, ?, ?, ?)',
                      (user_id, entry_date, mood, note))
    print("Inserted/verified 30 days of mood entries.")

    # Optional: Insert a test chat session and messages
    c.execute('SELECT id FROM chat_sessions WHERE user_id = ?', (user_id,))
    chat = c.fetchone()
    if chat:
        chat_id = chat[0]
    else:
        c.execute('INSERT INTO chat_sessions (user_id, title) VALUES (?, ?)', (user_id, 'Dummy Chat Session'))
        chat_id = c.lastrowid
    # Insert a few chat message pairs (user message, ai response)
    message_pairs = [
        ('Halo, ini pesan dummy pertama!', 'Halo testuser, bagaimana perasaanmu hari ini?'),
        ('Saya merasa cukup baik.', 'Senang mendengarnya!')
    ]
    for user_msg, ai_msg in message_pairs:
        c.execute('INSERT INTO chat_history (user_id, chat_id, message, response, timestamp) VALUES (?, ?, ?, ?, ?)',
                  (user_id, chat_id, user_msg, ai_msg, datetime.datetime.now()))
    print("Inserted dummy chat session and messages.")

    conn.commit()
    conn.close()
    print("Dummy data insertion complete.")

if __name__ == '__main__':
    main()
