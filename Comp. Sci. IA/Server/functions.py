import sqlite3
import flask

def login_verif(entereduser):
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username LIKE %"+entereduser+"%")
    results = cursor.fetchall
    if len(results) == 1:
        return True
