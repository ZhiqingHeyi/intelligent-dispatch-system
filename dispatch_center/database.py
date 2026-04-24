import sqlite3
import os
from config import LOCAL_DB, CONCRETE_GRADES

def get_db():
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS cable_car_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cable_car_id INTEGER UNIQUE NOT NULL,
        latitude REAL,
        longitude REAL,
        altitude REAL,
        xspeed REAL DEFAULT 0,
        yspeed REAL DEFAULT 0,
        direction TEXT DEFAULT '停止',
        start INTEGER DEFAULT 0,
        grade TEXT DEFAULT '',
        status TEXT DEFAULT '空闲',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS vehicle_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tid INTEGER UNIQUE NOT NULL,
        user_name TEXT DEFAULT '',
        result_x REAL,
        result_y REAL,
        speed REAL DEFAULT 0,
        direction TEXT DEFAULT '停止',
        grade TEXT DEFAULT '',
        status TEXT DEFAULT '空闲',
        target_cable_car_id INTEGER DEFAULT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS dispatch_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_tid INTEGER NOT NULL,
        cable_car_id INTEGER NOT NULL,
        grade TEXT NOT NULL,
        status TEXT DEFAULT '待执行',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        matched_at TIMESTAMP,
        completed_at TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS grade_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )''')

    for grade in CONCRETE_GRADES:
        c.execute('INSERT OR IGNORE INTO grade_config (name) VALUES (?)', (grade,))

    for i in range(1, 5):
        c.execute('INSERT OR IGNORE INTO cable_car_status (cable_car_id, direction, status) VALUES (?, ?, ?)',
                   (i, '停止', '空闲'))

    conn.commit()
    conn.close()
    print('数据库初始化完成')

if __name__ == '__main__':
    init_db()
