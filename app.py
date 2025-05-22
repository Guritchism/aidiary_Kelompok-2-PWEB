from flask import Flask, redirect, url_for, request, render_template, session, jsonify
from flask_session import Session
import sqlite3
from chat import gemini_create, conversation_history
import uuid
from datetime import datetime, timezone, timedelta
import json
import statistics
from collections import Counter
import re
import os

app = Flask(__name__)

# Setup SQLite database
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aidiary.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn

# Initialize database and create tables if they don't exist
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE
    )
    ''')
    
    # Create chat_history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        chat_id TEXT NOT NULL,
        message TEXT NOT NULL,
        response TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create mood_entries table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mood_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        mood INTEGER NOT NULL,
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create chat_sessions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize the database when the app starts
init_db()

app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = "filesystem"
Session(app)

def init_user_session():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())  # Unique ID for each user session

    if 'chats' not in session:
        session['chats'] = []
        session.modified = True
    else:
        updated = False
        for chat in session['chats']:
            if 'id' not in chat:
                chat['id'] = str(uuid.uuid4())
                updated = True
        if updated:
            session.modified = True

def sanitize_text(text):
    """
    Sanitizes text to ensure it can be stored in the database.
    Replaces problematic emoji or unicode characters with their text representation.
    """
    # Emoji dictionary for common emojis
    emoji_dict = {
        '😊': ':smile:',
        '😢': ':cry:',
        '😎': ':cool:',
        '☺️': ':happy:',
        '😁': ':grin:',
        '🙄': ':eyeroll:',
        '😡': ':angry:'
    }
    
    # Replace known emojis with text representation
    for emoji, replacement in emoji_dict.items():
        text = text.replace(emoji, replacement)
    
    # Remove any remaining emoji or problematic unicode characters
    # This regex matches emoji and other special characters that might cause problems
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251" 
        "]+"
    )
    
    text = emoji_pattern.sub(r'', text)
    
    return text

def load_chat_history_from_db(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First check if we have chat_history records with chat_id
        cursor.execute("PRAGMA table_info(chat_history)")
        columns = cursor.fetchall()
        has_chat_id_column = any(column[1] == 'chat_id' for column in columns)
        
        if has_chat_id_column:
            # Get all unique chat_ids for this user
            cursor.execute("""
                SELECT chat_id, MIN(timestamp) as first_timestamp
                FROM chat_history 
                WHERE user_id = ? 
                GROUP BY chat_id
                ORDER BY first_timestamp ASC
            """, (user_id,))
            
            chat_ids = cursor.fetchall()
            chats = []
            
            # For each chat_id, get its messages
            for chat_id_row in chat_ids:
                chat_id = chat_id_row[0]  # Extract chat_id from the result
                
                # Get the first message to use as chat name
                cursor.execute("""
                    SELECT message FROM chat_history 
                    WHERE user_id = ? AND chat_id = ? 
                    ORDER BY timestamp ASC LIMIT 1
                """, (user_id, chat_id))
                
                first_message = cursor.fetchone()
                chat_name = first_message[0][:30] + ('...' if len(first_message[0]) > 30 else '') if first_message else "Percakapan"
                
                # Get all messages for this chat
                cursor.execute("""
                    SELECT message, response, timestamp 
                    FROM chat_history 
                    WHERE user_id = ? AND chat_id = ?
                    ORDER BY timestamp ASC
                """, (user_id, chat_id))
                
                rows = cursor.fetchall()
                messages = []
                
                for row in rows:
                    messages.append({'role': 'user', 'content': row[0]})
                    messages.append({'role': 'assistant', 'content': row[1]})
                
                if messages:
                    chats.append({
                        "id": chat_id,
                        "name": chat_name,
                        "messages": messages
                    })
            
            conn.close()
            return chats
        
        else:
            # Legacy query for backward compatibility
            cursor.execute("""
                SELECT message, response, timestamp 
                FROM chat_history 
                WHERE user_id = ? 
                ORDER BY timestamp ASC
            """, (user_id,))
            
            rows = cursor.fetchall()
            messages = []
            
            for row in rows:
                messages.append({'role': 'user', 'content': row[0]})
                messages.append({'role': 'assistant', 'content': row[1]})
            
            conn.close()
            
            if messages:
                return [{
                    "id": str(uuid.uuid4()),
                    "name": "Riwayat Sebelumnya",
                    "messages": messages
                }]
        
        return []
    except Exception as e:
        app.logger.error(f"Error loading chat history: {e}")
        return []

# Tambahkan fungsi baru untuk memeriksa apakah user sudah entry mood hari ini
def has_mood_entry_today(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT id FROM mood_entries 
            WHERE user_id = ? AND date = ?
        """, (user_id, today))
        
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        app.logger.error(f"Error checking mood entry: {e}")
        return False

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        if 'login' in request.form:
            try:
                username = request.form['username']
                password = request.form['password']
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                user = cursor.fetchone()
                if user:
                    if user['password'] == password:
                        session['username'] = username
                        session['user_id'] = user['id']
                        conn.close()
                        return redirect(url_for('chat'))
                    else:
                        error = 'Password salah.'
                else:
                    # Check if any user exists with this password (for completeness, but not recommended for security)
                    cursor.execute('SELECT * FROM users WHERE password = ?', (password,))
                    user_by_pw = cursor.fetchone()
                    if user_by_pw:
                        error = 'Username salah.'
                    else:
                        error = 'Akun tidak ditemukan.'
                conn.close()
            except Exception as e:
                app.logger.error(f"Login error: {e}")
                error = 'Terjadi kesalahan saat login. Silakan coba lagi.'
        elif 'register' in request.form:
            try:
                username = request.form['username']
                password = request.form['password']
                email = request.form['email']
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', (username, password, email))
                conn.commit()
                conn.close()
            except sqlite3.IntegrityError: # Catch specific error for unique constraint
                error = "Username atau email sudah terdaftar."
            except Exception as e:
                app.logger.error(f"Registration error: {e}")
                error = 'Terjadi kesalahan saat registrasi. Silakan coba lagi.'
    
    # Pass login status and username to the template
    logged_in = 'username' in session
    current_username = session.get('username')
    return render_template('index.html', error=error, logged_in=logged_in, current_username=current_username)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('index'))

    init_user_session()

    # Cek apakah user sudah mengisi mood hari ini
    mood_today = has_mood_entry_today(session['user_id'])
    session['has_mood_today'] = mood_today
    
    # Jika session['chats'] kosong (misalnya setelah login baru atau tidak ada histori), muat dari database
    if not session['chats']:
        session['chats'] = load_chat_history_from_db(session['user_id'])
        session.modified = True

    # Jika user belum mengisi mood hari ini, langsung tampilkan mood prompt (pop up)
    show_mood_prompt = not mood_today

    if session['chats']:
        first_chat_id = session['chats'][0]['id']
        return redirect(url_for('open_chat', chat_id=first_chat_id, show_mood_prompt=show_mood_prompt))
    else:
        return render_template('chat.html', chats=[], selected_chat=None, show_mood_prompt=show_mood_prompt)

@app.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.form['message']
    chat_id = request.form.get('chat_id')  # use form data for consistency

    # Find selected chat
    selected_chat = next((chat for chat in session['chats'] if chat['id'] == chat_id), None)

    output = None # Inisialisasi output

    if selected_chat:
        # Pastikan kita menggunakan conversation_history dari chat.py
        # Buat history dalam format List[Tuple[str, str]] yang diharapkan oleh chat.conversation_history
        history_tuples = []
        temp_messages = selected_chat['messages']
        for i in range(0, len(temp_messages) - 1, 2):
            if temp_messages[i]['role'] == 'user' and temp_messages[i+1]['role'] == 'assistant':
                history_tuples.append((temp_messages[i]['content'], temp_messages[i+1]['content']))
        
        # Panggil conversation_history dari modul chat
        updated_history_tuples, _ = conversation_history(user_message, history_tuples) # Ini akan memanggil chat.conversation_history
        
        if updated_history_tuples:
            output = updated_history_tuples[-1][1] # Respons AI terbaru
            selected_chat['messages'].append({'role': 'user', 'content': user_message})
            selected_chat['messages'].append({'role': 'assistant', 'content': output})

            if selected_chat['name'].startswith('Percakapan') and len(selected_chat['messages']) == 2: # Hanya user pertama dan AI pertama
                selected_chat['name'] = user_message[:30] + ('...' if len(user_message) > 30 else '')
            
            session.modified = True

            # Simpan ke database
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Check if chat_id column exists
                cursor.execute("PRAGMA table_info(chat_history)")
                columns = cursor.fetchall()
                has_chat_id_column = any(column[1] == 'chat_id' for column in columns)
                
                # Sanitasi teks untuk menangani emoji
                sanitized_message = sanitize_text(user_message)
                sanitized_output = sanitize_text(output)
                
                if has_chat_id_column:
                    cursor.execute("""
                        INSERT INTO chat_history (user_id, chat_id, message, response, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    """, (session.get('user_id'), chat_id, sanitized_message, sanitized_output, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                else:
                    cursor.execute("""
                        INSERT INTO chat_history (user_id, message, response, timestamp)
                        VALUES (?, ?, ?, ?)
                    """, (session.get('user_id'), sanitized_message, sanitized_output, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                
                conn.commit()
                conn.close()
            except Exception as e:
                app.logger.error(f"DB insert error: {e}")  # log database errors
                # Optionally rollback or handle cleanup
        else:
            # Jika conversation_history tidak mengembalikan apa-apa atau error
            output = "Maaf, terjadi kesalahan saat memproses pesan Anda."
            # Anda mungkin ingin menambahkan pesan error ini ke selected_chat['messages'] juga
            selected_chat['messages'].append({'role': 'user', 'content': user_message})
            selected_chat['messages'].append({'role': 'assistant', 'content': output})
            session.modified = True


    else:
        # Kasus jika chat_id tidak ditemukan atau tidak disediakan.
        # Ini seharusnya tidak terjadi jika UI selalu mengirim chat_id yang valid
        # atau jika ini adalah pesan pertama untuk chat yang baru saja dibuat melalui /new_chat
        # Untuk chat baru, history_for_api harus kosong.
        # Kita panggil gemini_create langsung dari chat.py
        output = gemini_create(user_message, []) # Menyediakan history_for_api kosong
        # Jika ini terjadi, kita perlu memutuskan bagaimana menangani penyimpanan pesan ini.
        # Apakah kita membuat chat baru di sini, atau mengembalikan error?
        # Untuk saat ini, kita hanya akan mengembalikan outputnya.
        # Idealnya, UI harus memastikan chat_id yang valid selalu ada.
        # Atau, jika ini adalah bagian dari pembuatan chat baru, logika itu harus ada di /new_chat atau di sini.

    if output is None: # Fallback jika output belum di-set
        output = "Gagal mendapatkan respons dari AI."

    return jsonify({"user": user_message, "assistant": output})

@app.route('/new_chat', methods=['POST'])
def new_chat():
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 401

    init_user_session()
    
    # Generate a unique chat ID
    chat_id = str(uuid.uuid4())
    
    new_chat = {
        "id": chat_id,
        "name": f"Percakapan {len(session['chats']) + 1}",
        "messages": []
    }
    session['chats'].append(new_chat)
    session.modified = True

    return jsonify({"id": new_chat["id"], "name": new_chat["name"]})

@app.route('/chat/<chat_id>')
def open_chat(chat_id):
    if 'username' not in session:
        return redirect(url_for('index'))

    init_user_session()
    
    # Cek apakah user sudah mengisi mood hari ini jika belum pernah dicek
    if 'has_mood_today' not in session:
        mood_today = has_mood_entry_today(session['user_id'])
        session['has_mood_today'] = mood_today
    
    # Pastikan session['chats'] telah dimuat
    if not session.get('chats'):
        session['chats'] = load_chat_history_from_db(session['user_id'])
        session.modified = True
    
    # Find the selected chat
    selected_chat = next((chat for chat in session['chats'] if chat['id'] == chat_id), None)
    
    # If chat not found but should exist in db, load chats again
    if not selected_chat:
        session['chats'] = load_chat_history_from_db(session['user_id'])
        session.modified = True
        # Try to find the chat again
        selected_chat = next((chat for chat in session['chats'] if chat['id'] == chat_id), None)
    
    # Ambil show_mood_prompt dari query string jika ada
    show_mood_prompt = request.args.get('show_mood_prompt', 'False') == 'True'
    if selected_chat:
        return render_template('chat.html', chats=session['chats'], selected_chat=selected_chat, 
                              show_mood_prompt=show_mood_prompt)
    else:
        return "Percakapan tidak ditemukan", 404

@app.route('/mood-tracker')
def mood_tracker():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    # Menyediakan tanggal hari ini untuk formulir
    today_date = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('mood_tracker.html', today_date=today_date)

@app.route('/save_mood', methods=['POST'])
def save_mood():
    if 'username' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    try:
        date = request.form['date']
        mood = int(request.form['mood'])
        note = request.form['note']
        user_id = session['user_id']
        
        # Validasi input
        if mood < 1 or mood > 5:
            return jsonify({"success": False, "error": "Nilai mood tidak valid"})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Cek apakah sudah ada entri untuk tanggal ini
        cursor.execute("SELECT id FROM mood_entries WHERE user_id = ? AND date = ?", (user_id, date))
        existing_entry = cursor.fetchone()
        
        if existing_entry:
            # Update entri yang ada
            cursor.execute("""
                UPDATE mood_entries 
                SET mood = ?, note = ?, updated_at = ?
                WHERE id = ?
            """, (mood, note, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), existing_entry[0]))
            mood_id = existing_entry[0]
        else:
            # Buat entri baru
            cursor.execute("""
                INSERT INTO mood_entries (user_id, date, mood, note, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, date, mood, note, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            mood_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "mood_id": mood_id})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/get_mood_data')
def get_mood_data():
    if 'username' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    try:
        timeframe = request.args.get('timeframe', 'week')
        user_id = session['user_id']
        
        # Tentukan rentang tanggal berdasarkan timeframe
        today = datetime.now().date()
        if timeframe == 'week':
            start_date = today - timedelta(days=6)  # 7 hari termasuk hari ini
            date_format = '%d/%m'  # Format tanggal untuk label chart
        elif timeframe == 'month':
            start_date = today - timedelta(days=29)  # 30 hari termasuk hari ini
            date_format = '%d/%m'
        elif timeframe == 'year':
            start_date = today - timedelta(days=364)  # 365 hari termasuk hari ini
            date_format = '%b'  # Format bulan untuk label chart
        else:
            start_date = today - timedelta(days=6)  # Default ke week
            date_format = '%d/%m'
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ambil data mood dalam range waktu yang diminta
        cursor.execute("""
            SELECT id, date, mood, note, created_at 
            FROM mood_entries 
            WHERE user_id = ? AND date >= ? AND date <= ?
            ORDER BY date ASC
        """, (user_id, start_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')))
        
        rows = cursor.fetchall()
        mood_data = []
        for row in rows:
            mood_data.append({
                'id': row[0],
                'date': row[1],
                'mood': row[2],
                'note': row[3],
                'created_at': row[4]
            })
        
        conn.close()
        
        # Buat data untuk chart
        chart_data = prepare_chart_data(mood_data, start_date, today, date_format, timeframe)
        
        # Generate insights berdasarkan data mood
        insights = generate_mood_insights(mood_data, timeframe)
        
        # Return data untuk frontend
        return jsonify({
            "success": True,
            "chart_data": chart_data,
            "history": mood_data,
            "insights": insights
        })
    
    except Exception as e:
        app.logger.error(f"Error in get_mood_data: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/delete_mood', methods=['POST'])
def delete_mood():
    if 'username' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    try:
        mood_id = request.form['mood_id']
        user_id = session['user_id']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verifikasi bahwa entri milik user ini
        cursor.execute("SELECT id FROM mood_entries WHERE id = ? AND user_id = ?", (mood_id, user_id))
        if not cursor.fetchone():
            return jsonify({"success": False, "error": "Entri tidak ditemukan atau tidak memiliki izin"})
        
        # Hapus entri
        cursor.execute("DELETE FROM mood_entries WHERE id = ?", (mood_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def prepare_chart_data(mood_data, start_date, end_date, date_format, timeframe):
    """
    Menyiapkan data untuk chart berdasarkan entri mood
    """
    # Buat dictionary untuk memetakan tanggal ke mood
    date_to_mood = {item['date']: item for item in mood_data}
    
    # Generate range tanggal
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        date_range.append(date_str)
        current_date += timedelta(days=1)
    
    # Siapkan data chart
    labels = []
    values = []
    colors = []
    notes = []
    
    # Function untuk mendapatkan warna berdasarkan nilai mood
    def get_mood_color(mood_value):
        color_map = {
            1: '#F44336',  # Sangat Sedih
            2: '#FF9800',  # Sedih
            3: '#FFD54F',  # Netral
            4: '#AED581',  # Senang
            5: '#8BC34A'   # Sangat Senang
        }
        return color_map.get(mood_value, '#9E9E9E')
    
    # Konsolidasi data untuk chart tahunan jika diperlukan (rata-rata per bulan)
    if timeframe == 'year':
        monthly_moods = {}
        monthly_counts = {}
        
        for date_str in date_range:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            month_str = date_obj.strftime('%Y-%m')
            
            if date_str in date_to_mood:
                mood = date_to_mood[date_str]['mood']
                monthly_moods[month_str] = monthly_moods.get(month_str, 0) + mood
                monthly_counts[month_str] = monthly_counts.get(month_str, 0) + 1
        
        # Generate data chart per bulan
        months_in_range = []
        current_month = start_date
        while current_month <= end_date:
            month_str = current_month.strftime('%Y-%m')
            if month_str not in months_in_range:
                months_in_range.append(month_str)
            current_month += timedelta(days=28)  # Perkiraan satu bulan
        
        for month_str in months_in_range:
            date_obj = datetime.strptime(f"{month_str}-01", '%Y-%m-%d')
            labels.append(date_obj.strftime(date_format))
            
            if month_str in monthly_moods and monthly_counts[month_str] > 0:
                avg_mood = monthly_moods[month_str] / monthly_counts[month_str]
                values.append(round(avg_mood, 1))
                colors.append(get_mood_color(round(avg_mood)))
                notes.append(f"Rata-rata mood: {avg_mood:.1f}")
            else:
                values.append(None)
                colors.append('#9E9E9E')
                notes.append("Tidak ada data")
    else:
        # Generate data chart per hari
        for date_str in date_range:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            labels.append(date_obj.strftime(date_format))
            
            if date_str in date_to_mood:
                mood_entry = date_to_mood[date_str]
                values.append(mood_entry['mood'])
                colors.append(get_mood_color(mood_entry['mood']))
                notes.append(mood_entry['note'] if mood_entry['note'] else "")
            else:
                values.append(None)
                colors.append('#9E9E9E')
                notes.append("")
    
    return {
        'labels': labels,
        'values': values,
        'colors': colors,
        'notes': notes
    }

def generate_mood_insights(mood_data, timeframe):
    """
    Generate insights dan rekomendasi berdasarkan data mood
    """
    if not mood_data:
        return {
            'weekly_trend': "Belum ada data suasana hati yang cukup untuk analisis.",
            'best_day': "Belum ada data suasana hati yang cukup untuk analisis.",
            'suggestion': "Mulailah mencatat suasana hati Anda secara teratur untuk mendapatkan wawasan yang lebih baik."
        }
    
    # Ekstrak nilai mood dan tanggalnya
    moods = [entry['mood'] for entry in mood_data]
    dates = [datetime.strptime(entry['date'], '%Y-%m-%d') if isinstance(entry['date'], str) else entry['date'] for entry in mood_data]
    
    # Cari tren mingguan
    weekly_trend = "Belum ada pola yang jelas dalam suasana hati Anda."
    if len(moods) >= 3:
        if moods[-1] > moods[0]:
            weekly_trend = "Suasana hati Anda membaik dalam periode ini."
        elif moods[-1] < moods[0]:
            weekly_trend = "Suasana hati Anda menurun dalam periode ini."
        elif statistics.mean(moods[-3:]) > statistics.mean(moods[:3]):
            weekly_trend = "Akhir-akhir ini suasana hati Anda cenderung lebih baik."
        elif statistics.mean(moods[-3:]) < statistics.mean(moods[:3]):
            weekly_trend = "Akhir-akhir ini suasana hati Anda cenderung kurang baik."
    
    # Cari hari terbaik
    best_day = "Belum ada data yang cukup untuk menentukan hari terbaik Anda."
    if len(dates) >= 5:
        day_moods = {}
        for i, date in enumerate(dates):
            day_name = date.strftime('%A')  # Nama hari dalam bahasa Inggris
            if day_name not in day_moods:
                day_moods[day_name] = []
            day_moods[day_name].append(moods[i])
        
        # Hitung rata-rata mood per hari
        day_avg_moods = {}
        for day, day_mood_list in day_moods.items():
            if day_mood_list:
                day_avg_moods[day] = sum(day_mood_list) / len(day_mood_list)
        
        if day_avg_moods:
            # Temukan hari dengan mood tertinggi
            best_day_value = -1
            best_day_name = ""
            for day, avg_mood in day_avg_moods.items():
                if avg_mood > best_day_value:
                    best_day_value = avg_mood
                    best_day_name = day
            
            # Terjemahkan nama hari ke Bahasa Indonesia
            day_translation = {
                'Monday': 'Senin',
                'Tuesday': 'Selasa',
                'Wednesday': 'Rabu',
                'Thursday': 'Kamis',
                'Friday': 'Jumat',
                'Saturday': 'Sabtu',
                'Sunday': 'Minggu'
            }
            translated_day = day_translation.get(best_day_name, best_day_name)
            best_day = f"{translated_day} adalah hari dengan suasana hati terbaik Anda."
    
    # Generate saran
    suggestion = "Cobalah untuk mencatat apa yang membuat Anda bahagia dan ulangi aktivitas tersebut."
    avg_mood = statistics.mean(moods) if moods else 0
    
    if avg_mood < 2.5:
        suggestion = "Suasana hati Anda cenderung rendah. Pertimbangkan untuk berkonsultasi dengan profesional kesehatan mental."
    elif avg_mood < 3.5:
        suggestion = "Cobalah aktivitas yang dapat meningkatkan mood seperti olahraga ringan atau meditasi."
    else:
        suggestion = "Teruskan kebiasaan baik yang Anda lakukan. Anda cenderung memiliki suasana hati yang positif."
    
    return {
        'weekly_trend': weekly_trend,
        'best_day': best_day,
        'suggestion': suggestion
    }

@app.route('/check_mood_status')
def check_mood_status():
    if 'username' not in session:
        return jsonify({"loggedIn": False})
    
    # Periksa apakah sudah ada entri mood untuk hari ini
    has_mood = has_mood_entry_today(session['user_id'])
    
    # Update status di session
    session['has_mood_today'] = has_mood
    
    return jsonify({
        "loggedIn": True,
        "hasMoodToday": has_mood,
        "username": session['username']
    })

if __name__ == '__main__':
    app.run(debug=True)
