import sqlite3
import json
from config import DB_PATH, CONCRETE_GRADES

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS cable_cars (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        grade_id INTEGER DEFAULT 0,
        status TEXT DEFAULT 'idle',
        direction TEXT DEFAULT 'idle',
        state TEXT DEFAULT 'stopped',
        state_label TEXT DEFAULT '停止',
        manual_state TEXT DEFAULT 'normal',
        location TEXT DEFAULT '',
        latitude REAL DEFAULT 0,
        longitude REAL DEFAULT 0,
        altitude REAL DEFAULT 0,
        xspeed REAL DEFAULT 0,
        yspeed REAL DEFAULT 0,
        start INTEGER DEFAULT 0,
        updated_at TEXT,
        synced_at TEXT
    )''')
    
    # 迁移：添加 manual_state 列（如果不存在）
    try:
        c.execute('SELECT manual_state FROM cable_cars LIMIT 1')
    except:
        c.execute('ALTER TABLE cable_cars ADD COLUMN manual_state TEXT DEFAULT "normal"')
        conn.commit()
        print('[DB] 已添加 manual_state 列到 cable_cars 表')

    c.execute('''CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY,
        tid INTEGER NOT NULL,
        name TEXT NOT NULL,
        grade_id INTEGER DEFAULT 0,
        status TEXT DEFAULT 'idle',
        direction TEXT DEFAULT 'idle',
        state TEXT DEFAULT 'stopped',
        state_label TEXT DEFAULT '停止',
        location TEXT DEFAULT '',
        result_x REAL DEFAULT 0,
        result_y REAL DEFAULT 0,
        speed REAL DEFAULT 0,
        lat REAL DEFAULT 0,
        lon REAL DEFAULT 0,
        user_name TEXT DEFAULT '',
        route TEXT DEFAULT '',
        updated_at TEXT,
        synced_at TEXT
    )''')

    try:
        c.execute('SELECT state FROM vehicles LIMIT 1')
    except:
        c.execute('ALTER TABLE vehicles ADD COLUMN state TEXT DEFAULT "stopped"')
        c.execute('ALTER TABLE vehicles ADD COLUMN state_label TEXT DEFAULT "停止"')
        c.execute('ALTER TABLE vehicles ADD COLUMN location TEXT DEFAULT ""')
        conn.commit()
        print('[DB] 已添加 state, state_label, location 列到 vehicles 表')

    c.execute('''CREATE TABLE IF NOT EXISTS dispatch_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cable_car_id INTEGER NOT NULL,
        vehicle_id INTEGER NOT NULL,
        grade_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TEXT NOT NULL,
        assigned_at TEXT,
        completed_at TEXT,
        cancelled_at TEXT,
        note TEXT DEFAULT '',
        FOREIGN KEY (cable_car_id) REFERENCES cable_cars(id),
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS grade_config (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        color TEXT NOT NULL
    )''')

    for grade in CONCRETE_GRADES:
        c.execute('INSERT OR REPLACE INTO grade_config (id, name, color) VALUES (?, ?, ?)',
                  (grade['id'], grade['name'], grade['color']))

    for i in range(1, 5):
        c.execute('INSERT OR IGNORE INTO cable_cars (id, name) VALUES (?, ?)',
                  (i, f'{i}号缆机'))

    conn.commit()
    conn.close()

    try:
        from ai_experience import init_ai_tables
        init_ai_tables()
    except Exception as e:
        print(f'[DB] AI表初始化失败: {e}')

def reset_vehicle_grades():
    conn = get_db()
    conn.execute('UPDATE vehicles SET grade_id = 0')
    conn.commit()
    conn.close()

def update_cable_car_grade(car_id, grade_id):
    conn = get_db()
    conn.execute('UPDATE cable_cars SET grade_id = ? WHERE id = ?', (grade_id, car_id))
    conn.commit()
    conn.close()

def update_cable_car_state(car_id, manual_state):
    conn = get_db()
    conn.execute('UPDATE cable_cars SET manual_state = ? WHERE id = ?', (manual_state, car_id))
    conn.commit()
    conn.close()

def update_vehicle_grade(vehicle_id, grade_id):
    conn = get_db()
    conn.execute('UPDATE vehicles SET grade_id = ? WHERE id = ?', (grade_id, vehicle_id))
    conn.commit()
    conn.close()

def create_dispatch_task(cable_car_id, vehicle_id, grade_id):
    conn = get_db()
    from datetime import datetime
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor = conn.execute(
        'INSERT INTO dispatch_tasks (cable_car_id, vehicle_id, grade_id, status, created_at) VALUES (?, ?, ?, ?, ?)',
        (cable_car_id, vehicle_id, grade_id, 'assigned', now)
    )
    conn.execute('UPDATE cable_cars SET status = ? WHERE id = ?', ('assigned', cable_car_id))
    conn.execute('UPDATE vehicles SET status = ? WHERE id = ?', ('assigned', vehicle_id))
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return task_id

def complete_dispatch_task(task_id):
    conn = get_db()
    from datetime import datetime
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    task = conn.execute('SELECT cable_car_id, vehicle_id FROM dispatch_tasks WHERE id = ?', (task_id,)).fetchone()
    if task:
        conn.execute('UPDATE dispatch_tasks SET status = ?, completed_at = ? WHERE id = ?',
                      ('completed', now, task_id))
        conn.execute('UPDATE cable_cars SET status = ?, grade_id = 0 WHERE id = ?',
                      ('idle', task['cable_car_id']))
        conn.execute('UPDATE vehicles SET status = ?, grade_id = 0 WHERE id = ?',
                      ('idle', task['vehicle_id']))
    conn.commit()
    conn.close()

def cancel_dispatch_task(task_id):
    conn = get_db()
    from datetime import datetime
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    task = conn.execute('SELECT cable_car_id, vehicle_id FROM dispatch_tasks WHERE id = ?', (task_id,)).fetchone()
    if task:
        conn.execute('UPDATE dispatch_tasks SET status = ?, cancelled_at = ? WHERE id = ?',
                      ('cancelled', now, task_id))
        conn.execute('UPDATE cable_cars SET status = ?, grade_id = 0 WHERE id = ?',
                      ('idle', task['cable_car_id']))
        conn.execute('UPDATE vehicles SET status = ?, grade_id = 0 WHERE id = ?',
                      ('idle', task['vehicle_id']))
    conn.commit()
    conn.close()
