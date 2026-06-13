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

def save_session(data, ai_response, score_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO sessions 
        (date, symptoms, duration, severity, ai_response, score, assessment)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
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
    print("✅ Session saved to database")

def get_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, date, symptoms, score, assessment 
        FROM sessions 
        ORDER BY id DESC 
        LIMIT 5
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    return rows