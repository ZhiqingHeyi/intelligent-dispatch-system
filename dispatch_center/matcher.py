from database import get_db

def find_returning_cable_cars():
    db = get_db()
    c = db.cursor()
    c.execute("""
        SELECT cable_car_id, latitude, xspeed, yspeed, direction, grade, status
        FROM cable_car_status
        WHERE direction = '返程(往回走)' AND status != '已匹配'
        ORDER BY cable_car_id
    """)
    rows = c.fetchall()
    db.close()
    return [dict(r) for r in rows]

def find_going_vehicles(grade=None):
    db = get_db()
    c = db.cursor()
    if grade:
        c.execute("""
            SELECT tid, user_name, result_x, result_y, speed, direction, grade, status, target_cable_car_id
            FROM vehicle_status
            WHERE direction = '往程(送料)' AND grade = ? AND status = '空闲'
            ORDER BY speed DESC
        """, (grade,))
    else:
        c.execute("""
            SELECT tid, user_name, result_x, result_y, speed, direction, grade, status, target_cable_car_id
            FROM vehicle_status
            WHERE direction = '往程(送料)' AND status = '空闲'
            ORDER BY speed DESC
        """)
    rows = c.fetchall()
    db.close()
    return [dict(r) for r in rows]

def match_vehicle_to_cable_car():
    db = get_db()
    c = db.cursor()

    c.execute("""
        SELECT cable_car_id, latitude, xspeed, yspeed, direction, grade, status
        FROM cable_car_status
        WHERE direction = '返程(往回走)' AND status IN ('空闲', '等待中')
    """)
    returning_cars = [dict(r) for r in c.fetchall()]

    matches = []

    for car in returning_cars:
        if not car['grade']:
            continue

        c.execute("""
            SELECT tid, user_name, result_x, result_y, speed, direction, grade, status
            FROM vehicle_status
            WHERE direction = '往程(送料)' AND grade = ? AND status = '空闲'
            ORDER BY speed DESC
            LIMIT 1
        """, (car['grade'],))
        vehicle = c.fetchone()

        if vehicle:
            vehicle = dict(vehicle)
            matches.append({
                'cable_car_id': car['cable_car_id'],
                'vehicle_tid': vehicle['tid'],
                'grade': car['grade'],
                'vehicle_name': vehicle['user_name']
            })

    db.close()
    return matches

def create_dispatch_task(cable_car_id, vehicle_tid, grade):
    db = get_db()
    c = db.cursor()

    c.execute("""
        INSERT INTO dispatch_tasks (vehicle_tid, cable_car_id, grade, status, created_at)
        VALUES (?, ?, ?, '待执行', datetime('now'))
    """, (vehicle_tid, cable_car_id, grade))

    c.execute("""
        UPDATE cable_car_status SET status = '已匹配' WHERE cable_car_id = ?
    """, (cable_car_id,))

    c.execute("""
        UPDATE vehicle_status SET status = '已匹配', target_cable_car_id = ? WHERE tid = ?
    """, (cable_car_id, vehicle_tid))

    db.commit()
    db.close()
    return True

def complete_dispatch_task(task_id):
    db = get_db()
    c = db.cursor()

    c.execute('SELECT vehicle_tid, cable_car_id FROM dispatch_tasks WHERE id = ?', (task_id,))
    task = c.fetchone()
    if not task:
        db.close()
        return False

    vehicle_tid = task['vehicle_tid']
    cable_car_id = task['cable_car_id']

    c.execute("""
        UPDATE dispatch_tasks SET status = '已完成', completed_at = datetime('now') WHERE id = ?
    """, (task_id,))

    c.execute("""
        UPDATE cable_car_status SET status = '空闲', grade = '' WHERE cable_car_id = ?
    """, (cable_car_id,))

    c.execute("""
        UPDATE vehicle_status SET status = '空闲', target_cable_car_id = NULL, grade = '' WHERE tid = ?
    """, (vehicle_tid,))

    db.commit()
    db.close()
    return True

def cancel_dispatch_task(task_id):
    db = get_db()
    c = db.cursor()

    c.execute('SELECT vehicle_tid, cable_car_id FROM dispatch_tasks WHERE id = ?', (task_id,))
    task = c.fetchone()
    if not task:
        db.close()
        return False

    vehicle_tid = task['vehicle_tid']
    cable_car_id = task['cable_car_id']

    c.execute('UPDATE dispatch_tasks SET status = ? WHERE id = ?', ('已取消', task_id))

    c.execute('UPDATE cable_car_status SET status = ? WHERE cable_car_id = ?', ('空闲', cable_car_id))
    c.execute('UPDATE vehicle_status SET status = ?, target_cable_car_id = NULL WHERE tid = ?', ('空闲', vehicle_tid))

    db.commit()
    db.close()
    return True

def get_all_dispatch_tasks():
    db = get_db()
    c = db.cursor()
    c.execute("""
        SELECT t.*, v.user_name as vehicle_name
        FROM dispatch_tasks t
        LEFT JOIN vehicle_status v ON t.vehicle_tid = v.tid
        ORDER BY t.created_at DESC
    """)
    rows = c.fetchall()
    db.close()
    return [dict(r) for r in rows]

def get_dispatch_stats():
    db = get_db()
    c = db.cursor()

    c.execute('SELECT COUNT(*) as total FROM dispatch_tasks')
    total = c.fetchone()['total']

    c.execute("SELECT COUNT(*) as cnt FROM dispatch_tasks WHERE status = '待执行'")
    pending = c.fetchone()['cnt']

    c.execute("SELECT COUNT(*) as cnt FROM dispatch_tasks WHERE status = '已完成'")
    completed = c.fetchone()['cnt']

    c.execute("SELECT COUNT(*) as cnt FROM cable_car_status WHERE direction = '返程(往回走)'")
    returning = c.fetchone()['cnt']

    c.execute("SELECT COUNT(*) as cnt FROM vehicle_status WHERE direction = '往程(送料)'")
    going = c.fetchone()['cnt']

    db.close()
    return {
        'total_tasks': total,
        'pending_tasks': pending,
        'completed_tasks': completed,
        'returning_cars': returning,
        'going_vehicles': going
    }
