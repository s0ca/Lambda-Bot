# init_db.py
import sqlite3

def init_db():
    conn = sqlite3.connect('notes.db')
    cursor = conn.cursor()

    # Créez une table avec un ID unique auto-incrémenté pour chaque note
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY,
            user_id TEXT,
            note TEXT
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("La base de données a été initialisée avec succès.")
