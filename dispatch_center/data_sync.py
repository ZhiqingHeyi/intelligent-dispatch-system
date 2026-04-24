import pymysql
import threading
import time
from config import SOURCE_DB, SYNC_INTERVAL, CABLE_CAR_RETURN_THRESHOLD, VEHICLE_GOING_THRESHOLD
from database import get_db

def get_cable_car_direction(xspeed, start):
    if start == 0:
        return '停止'
    if xspeed > 0.5:
        return '往程(送料)'
    elif xspeed < CABLE_CAR_RETURN_THRESHOLD:
        return '返程(往回走)'
    elif abs(xspeed) <= 0.5:
        return '调整中'
    else:
        return '运行中'

def get_vehicle_direction(prev_y, curr_y):
    if prev_y is None:
        return '停止'
    delta = curr_y - prev_y
    if delta < VEHICLE_GOING_THRESHOLD:
        return '往程(送料)'
    elif delta > abs(VEHICLE_GOING_THRESHOLD):
        return '返程'
    else:
        return '停止'

def get_vehicle_zone(result_y):
    if result_y > -400:
        return '右端起点区'
    elif result_y > -800:
        return '中途区'
    else:
        return '左端终点区'

def sync_cable_car_data():
    try:
        conn_src = pymysql.connect(**SOURCE_DB['cable_car'])
        cursor_src = conn_src.cursor()
        cursor_src.execute("""
            SELECT cable_car_id, latitude, longitude, altitude, start, xspeed, yspeed
            FROM cable_car_status
            ORDER BY cable_car_id
        """)
        rows = cursor_src.fetchall()
        conn_src.close()

        db = get_db()
        c = db.cursor()
        for row in rows:
            cable_car_id = row[0]
            latitude = float(row[1]) if row[1] else 0
            longitude = float(row[2]) if row[2] else 0
            altitude = float(row[3]) if row[3] else 0
            start = row[4]
            xspeed = float(row[5]) if row[5] else 0
            yspeed = float(row[6]) if row[6] else 0

            direction = get_cable_car_direction(xspeed, start)

            c.execute("""
                INSERT INTO cable_car_status (cable_car_id, latitude, longitude, altitude, start, xspeed, yspeed, direction, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(cable_car_id) DO UPDATE SET
                    latitude=excluded.latitude,
                    longitude=excluded.longitude,
                    altitude=excluded.altitude,
                    start=excluded.start,
                    xspeed=excluded.xspeed,
                    yspeed=excluded.yspeed,
                    direction=excluded.direction,
                    updated_at=datetime('now')
            """, (cable_car_id, latitude, longitude, altitude, start, xspeed, yspeed, direction))

        db.commit()
        db.close()
        return True
    except Exception as e:
        print(f'同步缆机数据失败: {e}')
        return False

def sync_vehicle_data():
    try:
        conn_src = pymysql.connect(**SOURCE_DB['vehicle_system'])
        cursor_src = conn_src.cursor()

        cursor_src.execute("""
            SELECT tid, user_name, result_x, result_y, speed, time
            FROM datum_data
            ORDER BY tid
        """)
        rows = cursor_src.fetchall()
        conn_src.close()

        db = get_db()
        c = db.cursor()

        for row in rows:
            tid = row[0]
            user_name = row[1] if row[1] else ''
            result_x = float(row[2]) if row[2] else 0
            result_y = float(row[3]) if row[3] else 0
            speed = float(row[4]) if row[4] else 0

            c.execute('SELECT result_y FROM vehicle_status WHERE tid = ?', (tid,))
            prev = c.fetchone()
            prev_y = prev['result_y'] if prev else None

            direction = get_vehicle_direction(prev_y, result_y)

            c.execute("""
                INSERT INTO vehicle_status (tid, user_name, result_x, result_y, speed, direction, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(tid) DO UPDATE SET
                    user_name=excluded.user_name,
                    result_x=excluded.result_x,
                    result_y=excluded.result_y,
                    speed=excluded.speed,
                    direction=excluded.direction,
                    updated_at=datetime('now')
            """, (tid, user_name, result_x, result_y, speed, direction))

        db.commit()
        db.close()
        return True
    except Exception as e:
        print(f'同步车辆数据失败: {e}')
        return False

def sync_all():
    r1 = sync_cable_car_data()
    r2 = sync_vehicle_data()
    return r1 and r2

_sync_thread = None
_sync_running = False

def start_sync_loop():
    global _sync_thread, _sync_running
    if _sync_running:
        return
    _sync_running = True

    def loop():
        while _sync_running:
            sync_all()
            time.sleep(SYNC_INTERVAL)

    _sync_thread = threading.Thread(target=loop, daemon=True)
    _sync_thread.start()
    print('数据同步服务已启动')

def stop_sync_loop():
    global _sync_running
    _sync_running = False
    print('数据同步服务已停止')

if __name__ == '__main__':
    sync_all()
    print('同步完成')
