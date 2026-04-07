import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / 'swim_results.db'


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = connect()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS swimmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            gender TEXT,
            birth_year INTEGER
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            swimmer_id INTEGER NOT NULL,
            meet_name TEXT,
            event_name TEXT,
            course TEXT,
            time_text TEXT,
            rank_text TEXT,
            meet_date TEXT,
            source_url TEXT,
            is_pb INTEGER DEFAULT 0,
            FOREIGN KEY (swimmer_id) REFERENCES swimmers(id)
        )
    ''')
    conn.commit()
    conn.close()


def add_swimmer(name, gender=None, birth_year=None):
    conn = connect()
    cur = conn.cursor()
    cur.execute('INSERT INTO swimmers (name, gender, birth_year) VALUES (?, ?, ?)', (name, gender, birth_year))
    conn.commit()
    swimmer_id = cur.lastrowid
    conn.close()
    return swimmer_id


def get_swimmers():
    conn = connect()
    rows = conn.execute('SELECT * FROM swimmers ORDER BY id DESC').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_result(swimmer_id, meet_name, event_name, course, time_text, rank_text, meet_date, source_url=''):
    conn = connect()
    conn.execute(
        '''INSERT INTO results (swimmer_id, meet_name, event_name, course, time_text, rank_text, meet_date, source_url)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (swimmer_id, meet_name, event_name, course, time_text, rank_text, meet_date, source_url)
    )
    conn.commit()
    conn.close()


def get_results_for_swimmer(swimmer_id):
    conn = connect()
    rows = conn.execute('SELECT * FROM results WHERE swimmer_id = ? ORDER BY meet_date DESC, id DESC', (swimmer_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_results():
    conn = connect()
    rows = conn.execute('''
        SELECT r.*, s.name AS swimmer_name
        FROM results r
        JOIN swimmers s ON s.id = r.swimmer_id
        ORDER BY r.meet_date DESC, r.id DESC
    ''').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _time_to_seconds(text):
    if not text:
        return None
    t = text.strip()
    try:
        if ':' in t:
            mins, secs = t.split(':', 1)
            return int(mins) * 60 + float(secs)
        return float(t)
    except Exception:
        return None


def update_pb_cache(swimmer_id):
    conn = connect()
    rows = conn.execute('SELECT id, event_name, time_text FROM results WHERE swimmer_id = ?', (swimmer_id,)).fetchall()
    grouped = {}
    for row in rows:
        sec = _time_to_seconds(row['time_text'])
        if sec is None:
            continue
        grouped.setdefault(row['event_name'], []).append((row['id'], sec))

    conn.execute('UPDATE results SET is_pb = 0 WHERE swimmer_id = ?', (swimmer_id,))
    for _, items in grouped.items():
        best_id, _ = min(items, key=lambda x: x[1])
        conn.execute('UPDATE results SET is_pb = 1 WHERE id = ?', (best_id,))
    conn.commit()
    conn.close()
