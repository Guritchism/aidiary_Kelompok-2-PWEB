import sqlite3
import os
import uuid

# Create database path
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aidiary.db')

# Connect to database
conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

# Check if chat_history table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history'")
chat_history_exists = cursor.fetchone() is not None

if chat_history_exists:
    # Check if chat_id column exists in chat_history
    cursor.execute("PRAGMA table_info(chat_history)")
    columns = cursor.fetchall()
    
    has_chat_id_column = any(column[1] == 'chat_id' for column in columns)
    
    if not has_chat_id_column:
        print("Migrating database: Adding chat_id column to chat_history table")
        
        # Create temporary table with new schema
        cursor.execute('''
        CREATE TABLE chat_history_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            chat_id TEXT NOT NULL,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Get unique user_ids
        cursor.execute("SELECT DISTINCT user_id FROM chat_history")
        user_ids = cursor.fetchall()
        
        for user_id_row in user_ids:
            user_id = user_id_row[0]
            
            # Get all messages for this user sorted by timestamp
            cursor.execute("""
                SELECT id, user_id, message, response, timestamp 
                FROM chat_history 
                WHERE user_id = ? 
                ORDER BY timestamp ASC
            """, (user_id,))
            
            # Assuming all messages from the same user belong to one chat
            # We can create a new chat_id for this user
            chat_id = str(uuid.uuid4())
            
            # Transfer data with the new chat_id
            for row in cursor.fetchall():
                cursor.execute("""
                    INSERT INTO chat_history_new (user_id, chat_id, message, response, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (row[1], chat_id, row[2], row[3], row[4]))
        
        # Replace old table with new one
        cursor.execute("DROP TABLE chat_history")
        cursor.execute("ALTER TABLE chat_history_new RENAME TO chat_history")
        
        conn.commit()
        print("Migration complete")
    else:
        print("Database schema is already up to date")
else:
    print("chat_history table doesn't exist yet, no migration needed")

conn.close()
print("Database check completed")
