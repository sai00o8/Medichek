import sqlite3
import os
from datetime import datetime

DB_PATH = "medicheck.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            symptoms TEXT,
            duration TEXT,
            severity TEXT,
            ai_response TEXT,
            score INTEGER,
            assessment TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    
    init_users_table()

def init_users_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def create_user(username, email, password_hash):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
        ''', (username, email, password_hash, datetime.now().strftime("%Y-%m-%d %H:%M")))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    
    except sqlite3.IntegrityError:
        conn.close()
        return None  # username or email already exists

def get_user_by_username(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, username, email, password_hash FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    return row

def delete_session(user_id, session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM sessions WHERE id = ? AND user_id = ?', (session_id, user_id))
    affected = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return affected > 0

def delete_all_sessions(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
    
    conn.commit()
    conn.close()

def get_session_by_id(user_id, session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, date, symptoms, duration, severity, ai_response, score, assessment
        FROM sessions 
        WHERE id = ? AND user_id = ?
    ''', (session_id, user_id))
    
    row = cursor.fetchone()
    conn.close()
    return row

def search_sessions(user_id, keyword):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, date, symptoms, score, assessment 
        FROM sessions 
        WHERE user_id = ? AND symptoms LIKE ?
        ORDER BY id DESC
    ''', (user_id, f'%{keyword}%'))
    
    rows = cursor.fetchall()
    conn.close()
    return rows

def save_session(user_id, data, ai_response, score_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO sessions 
        (user_id, date, symptoms, duration, severity, ai_response, score, assessment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        data["symptoms"],
        data["duration"],
        data["severity"],
        ai_response,
        score_data["score"],
        score_data["severity_level"]
    ))
    
    conn.commit()
    conn.close()

def get_history(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, date, symptoms, score, assessment 
        FROM sessions 
        WHERE user_id = ?
        ORDER BY id DESC 
        LIMIT 5
    ''', (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    return rows