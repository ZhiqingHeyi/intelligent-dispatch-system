#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据同步模块 - 包含基于状态切换的智能匹配逻辑

匹配触发逻辑：
1. 缆机从 "返程途中(returning)" → "990平台接料(loading)" 触发匹配
2. 在接料期间持续寻找同级别送料车辆
3. 缆机从 "990平台接料(loading)" → "送料途中(delivering)" 结束匹配

任务完成逻辑（OR逻辑，任一触发即完成）：
触发源1: 缆机 loading → delivering（缆机开始送料，说明车已到装好料了）
触发源2: 车辆 going → returning（车辆开始返程，说明已送完料了）
兜底机制: auto_complete() 定期检查当前状态，防止状态切换事件丢失

状态流转：
返程途中 → 990平台接料 → 送料途中
    ↓           ↓              ↓
(卸完料)   (触发匹配)      (结束匹配+完成任务)
"""

import pymysql
import threading
import time
from collections import deque
from datetime import datetime
from config import CABLE_CAR_DB, VEHICLE_DB, SYNC_INTERVAL, VEHICLE_GOING_THRESHOLD
from database import get_db
from state_detector import (
    detect_cable_car_state, detect_vehicle_state,
    LOADING_ZONE, UNLOADING_ZONE,
    VEHICLE_LOADING_ZONE, VEHICLE_UNLOADING_ZONE, VEHICLE_Y_DELTA_THRESHOLD
)

VEHICLE_Y_HISTORY_SIZE = 5
VEHICLE_DIRECTION_CONFIRM_FRAMES = 2

_vehicle_y_history = {}
_vehicle_prev_direction = {}
_vehicle_direction_confirm = {}

_cable_car_prev_state = {}

_matching_cable_cars = {}


def _get_cable_car_conn():
    return pymysql.connect(**CABLE_CAR_DB)


def _get_vehicle_conn():
    return pymysql.connect(**VEHICLE_DB)


def detect_cable_car_direction(xspeed, start):
    if start == 0:
        return 'stopped'
    if xspeed > 0.5:
        return 'going'
    if xspeed < -0.5:
        return 'returning'
    return 'idle'


def detect_vehicle_direction(tid, result_y, speed):
    """检测车辆行驶方向 - 增强版（滑动窗口趋势 + 方向确认机制）"""
    global _vehicle_y_history, _vehicle_prev_direction, _vehicle_direction_confirm

    if tid not in _vehicle_y_history:
        _vehicle_y_history[tid] = deque(maxlen=VEHICLE_Y_HISTORY_SIZE)

    history = _vehicle_y_history[tid]
    history.append(result_y)

    if speed is None or float(speed) < 0.1:
        prev_dir = _vehicle_prev_direction.get(tid, 'idle')
        if prev_dir in ('going', 'returning'):
            return prev_dir
        return 'stopped'

    if len(history) < 2:
        _vehicle_prev_direction[tid] = 'idle'
        return 'idle'

    y_trend = 0
    hist_list = list(history)
    for i in range(1, len(hist_list)):
        y_trend += hist_list[i] - hist_list[i - 1]

    raw_direction = 'idle'
    if y_trend < VEHICLE_GOING_THRESHOLD:
        raw_direction = 'going'
    elif y_trend > abs(VEHICLE_GOING_THRESHOLD):
        raw_direction = 'returning'

    prev_dir = _vehicle_prev_direction.get(tid, 'idle')

    if raw_direction != 'idle' and raw_direction != prev_dir:
        confirm_key = f"{tid}_{raw_direction}"
        _vehicle_direction_confirm[confirm_key] = _vehicle_direction_confirm.get(confirm_key, 0) + 1

        other_key = f"{tid}_{'returning' if raw_direction == 'going' else 'going'}"
        _vehicle_direction_confirm[other_key] = 0

        if _vehicle_direction_confirm[confirm_key] >= VEHICLE_DIRECTION_CONFIRM_FRAMES:
            _vehicle_prev_direction[tid] = raw_direction
            _vehicle_direction_confirm[confirm_key] = 0
            return raw_direction
        else:
            return prev_dir if prev_dir in ('going', 'returning') else raw_direction
    else:
        if raw_direction == prev_dir:
            for key in list(_vehicle_direction_confirm.keys()):
                if key.startswith(f"{tid}_"):
                    _vehicle_direction_confirm[key] = 0
        return prev_dir if prev_dir in ('going', 'returning') else raw_direction


def _compute_vehicle_y_trend(tid):
    """计算车辆Y坐标的滑动窗口趋势"""
    history = _vehicle_y_history.get(tid)
    if not history or len(history) < 2:
        return 0
    hist_list = list(history)
    trend = 0
    for i in range(1, len(hist_list)):
        trend += hist_list[i] - hist_list[i - 1]
    return trend


def _try_complete_task_by_cable_car(car_id, local_db, now):
    """触发源1：缆机 loading → delivering 时尝试完成任务"""
    task = local_db.execute(
        '''SELECT id, vehicle_id FROM dispatch_tasks
           WHERE cable_car_id = ? AND status = 'assigned'
           LIMIT 1''',
        (car_id,)
    ).fetchone()

    if task:
        local_db.execute('UPDATE dispatch_tasks SET status = ?, completed_at = ? WHERE id = ?',
                         ('completed', now, task['id']))
        local_db.execute('UPDATE cable_cars SET status = ?, grade_id = 0 WHERE id = ?',
                         ('idle', car_id))
        local_db.execute('UPDATE vehicles SET status = ?, grade_id = 0 WHERE id = ?',
                         ('idle', task['vehicle_id']))
        print(f"[COMPLETE-CABLE] 任务#{task['id']} 已自动完成 ({car_id}号缆机开始送料)")
        return True
    return False


def _try_complete_task_by_vehicle(vehicle_id, local_db, now):
    """触发源2：车辆 going → returning 时尝试完成任务"""
    task = local_db.execute(
        '''SELECT id, cable_car_id FROM dispatch_tasks
           WHERE vehicle_id = ? AND status = 'assigned'
           LIMIT 1''',
        (vehicle_id,)
    ).fetchone()

    if task:
        local_db.execute('UPDATE dispatch_tasks SET status = ?, completed_at = ? WHERE id = ?',
                         ('completed', now, task['id']))
        local_db.execute('UPDATE cable_cars SET status = ?, grade_id = 0 WHERE id = ?',
                         ('idle', task['cable_car_id']))
        local_db.execute('UPDATE vehicles SET status = ?, grade_id = 0 WHERE id = ?',
                         ('idle', vehicle_id))
        print(f"[COMPLETE-VEHICLE] 任务#{task['id']} 已自动完成 (车辆{vehicle_id}已返程)")
        return True
    return False


def sync_cable_cars():
    """同步缆机数据并检测状态切换"""
    global _cable_car_prev_state

    try:
        conn = _get_cable_car_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cable_car_id, latitude, longitude, altitude, start, xspeed, yspeed, updated_at
            FROM cable_car_status
            ORDER BY cable_car_id
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        local_db = get_db()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for row in rows:
            car_id = row[0]
            latitude = float(row[1]) if row[1] else 0
            longitude = float(row[2]) if row[2] else 0
            altitude = float(row[3]) if row[3] else 0
            start = int(row[4]) if row[4] else 0
            xspeed = float(row[5]) if row[5] else 0
            yspeed = float(row[6]) if row[6] else 0
            updated_at = str(row[7]) if row[7] else now

            state, state_label, location = detect_cable_car_state(latitude, xspeed, start)

            direction = detect_cable_car_direction(xspeed, start)

            prev_state = _cable_car_prev_state.get(car_id)

            if prev_state and prev_state != state:
                print(f"[STATE] {car_id}号缆机状态切换: {prev_state} → {state}")

                if prev_state == 'returning' and state == 'loading':
                    print(f"[MATCH-TRIGGER] {car_id}号缆机到达装料区，开始匹配车辆")
                    _matching_cable_cars[car_id] = {
                        'start_time': now,
                        'matched': False,
                        'vehicle_id': None
                    }

                if prev_state == 'loading' and state == 'delivering':
                    if car_id in _matching_cable_cars:
                        match_info = _matching_cable_cars.pop(car_id)
                        if match_info['matched']:
                            print(f"[MATCH-END] {car_id}号缆机开始送料，匹配任务继续执行")
                        else:
                            print(f"[MATCH-END] {car_id}号缆机开始送料，未匹配到车辆（可能已人工调度）")

                    _try_complete_task_by_cable_car(car_id, local_db, now)

            _cable_car_prev_state[car_id] = state

            current = local_db.execute('SELECT status, grade_id FROM cable_cars WHERE id = ?', (car_id,)).fetchone()
            if current and current['status'] == 'assigned':
                local_db.execute('''UPDATE cable_cars SET latitude=?, longitude=?, altitude=?,
                    xspeed=?, yspeed=?, start=?, state=?, state_label=?, location=?, direction=?, updated_at=?, synced_at=?
                    WHERE id=?''',
                    (latitude, longitude, altitude, xspeed, yspeed, start,
                     state, state_label, location, direction, updated_at, now, car_id))
            else:
                if car_id in _matching_cable_cars and not _matching_cable_cars[car_id]['matched']:
                    new_status = 'matching'
                else:
                    new_status = state if state in ['loading', 'unloading', 'delivering', 'returning'] else 'idle'

                local_db.execute('''UPDATE cable_cars SET latitude=?, longitude=?, altitude=?,
                    xspeed=?, yspeed=?, start=?, state=?, state_label=?, location=?, direction=?, status=?, updated_at=?, synced_at=?
                    WHERE id=?''',
                    (latitude, longitude, altitude, xspeed, yspeed, start,
                     state, state_label, location, direction,
                     new_status, updated_at, now, car_id))

        local_db.commit()
        local_db.close()
        return True
    except Exception as e:
        print(f"[SYNC] cable_car sync error: {e}")
        import traceback
        traceback.print_exc()
        return False


def sync_vehicles():
    """同步车辆数据 - 增强版（状态识别 + 方向切换追踪 + 任务完成触发）"""
    global _vehicle_prev_direction

    try:
        conn = _get_vehicle_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tid, user_name, result_x, result_y, lat, lon, speed, time, route
            FROM datum_data
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        local_db = get_db()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for row in rows:
            tid = row[0]
            user_name = row[1] or ''
            result_x = float(row[2]) if row[2] else 0
            result_y = float(row[3]) if row[3] else 0
            lat = float(row[4]) if row[4] else 0
            lon = float(row[5]) if row[5] else 0
            speed = float(row[6]) if row[6] else 0
            updated_at = str(row[7]) if row[7] else now
            route = row[8] or ''

            prev_direction = _vehicle_prev_direction.get(tid, 'idle')
            direction = detect_vehicle_direction(tid, result_y, speed)

            y_trend = _compute_vehicle_y_trend(tid)
            v_state, v_state_label, v_location = detect_vehicle_state(result_y, speed, y_trend)

            if prev_direction in ('going', 'idle') and direction == 'returning':
                print(f"[VEHICLE-STATE] {tid}号车方向切换: {prev_direction} → returning")

            existing = local_db.execute('SELECT id, status, direction FROM vehicles WHERE tid = ?', (tid,)).fetchone()
            if existing:
                vehicle_id = existing['id']
                old_direction = existing['direction']

                if existing['status'] == 'assigned':
                    local_db.execute('''UPDATE vehicles SET result_x=?, result_y=?, speed=?, lat=?, lon=?,
                        user_name=?, route=?, direction=?, state=?, state_label=?, location=?,
                        updated_at=?, synced_at=?
                        WHERE tid=?''',
                        (result_x, result_y, speed, lat, lon, user_name, route, direction,
                         v_state, v_state_label, v_location,
                         updated_at, now, tid))

                    if old_direction != 'returning' and direction == 'returning':
                        _try_complete_task_by_vehicle(vehicle_id, local_db, now)
                else:
                    new_status = 'going' if direction == 'going' else 'idle'
                    local_db.execute('''UPDATE vehicles SET result_x=?, result_y=?, speed=?, lat=?, lon=?,
                        user_name=?, route=?, direction=?, status=?, state=?, state_label=?, location=?,
                        updated_at=?, synced_at=?
                        WHERE tid=?''',
                        (result_x, result_y, speed, lat, lon, user_name, route, direction,
                         new_status, v_state, v_state_label, v_location,
                         updated_at, now, tid))
            else:
                new_status = 'going' if direction == 'going' else 'idle'
                local_db.execute('''INSERT INTO vehicles (tid, name, grade_id, status, direction, result_x, result_y,
                    speed, lat, lon, user_name, route, state, state_label, location, updated_at, synced_at)
                    VALUES (?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (tid, user_name or f'{tid}号车',
                     new_status, direction,
                     result_x, result_y, speed, lat, lon, user_name, route,
                     v_state, v_state_label, v_location,
                     updated_at, now))

        local_db.commit()
        local_db.close()
        return True
    except Exception as e:
        print(f"[SYNC] vehicle sync error: {e}")
        import traceback
        traceback.print_exc()
        return False


def send_match_message_to_vehicle(vehicle_id, cable_car_id, grade_name):
    print(f"[MSG-RESERVE] 向车辆{vehicle_id}发送消息: 请前往{cable_car_id}号缆机({grade_name})")
    return True


def auto_match():
    """自动匹配逻辑"""
    global _matching_cable_cars

    try:
        db = get_db()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        matching_car_ids = [car_id for car_id, info in _matching_cable_cars.items()
                           if not info['matched']]

        if not matching_car_ids:
            db.close()
            return

        print(f"[MATCH] 当前有{len(matching_car_ids)}台缆机正在匹配中: {matching_car_ids}")

        cars = []
        for car_id in matching_car_ids:
            car = db.execute('SELECT * FROM cable_cars WHERE id = ?', (car_id,)).fetchone()
            if car:
                cars.append(dict(car))

        going_vehicles = [dict(r) for r in db.execute(
            '''SELECT * FROM vehicles
               WHERE direction = 'going' AND status = 'going' AND grade_id > 0
               AND id NOT IN (SELECT vehicle_id FROM dispatch_tasks WHERE status = 'assigned')'''
        ).fetchall()]

        if not going_vehicles:
            print(f"[MATCH] 暂无可用送料车辆")
            db.close()
            return

        print(f"[MATCH] 找到{len(going_vehicles)}台可用送料车辆")

        for car in cars:
            car_id = car['id']

            if car['grade_id'] == 0:
                print(f"[MATCH] {car_id}号缆机未设置级配，跳过匹配")
                continue

            matched_vehicle = None
            for v in going_vehicles:
                if v['grade_id'] == car['grade_id']:
                    matched_vehicle = v
                    break

            if matched_vehicle:
                print(f"[MATCH-SUCCESS] {car_id}号缆机({car.get('grade_name', '未知级配')}) ↔ {matched_vehicle['name']} 匹配成功")

                db.execute(
                    'INSERT INTO dispatch_tasks (cable_car_id, vehicle_id, grade_id, status, created_at, assigned_at) VALUES (?, ?, ?, ?, ?, ?)',
                    (car['id'], matched_vehicle['id'], car['grade_id'], 'assigned', now, now)
                )

                db.execute('UPDATE cable_cars SET status = ? WHERE id = ?', ('assigned', car['id']))
                db.execute('UPDATE vehicles SET status = ? WHERE id = ?', ('assigned', matched_vehicle['id']))

                _matching_cable_cars[car_id]['matched'] = True
                _matching_cable_cars[car_id]['vehicle_id'] = matched_vehicle['id']

                grade_name = matched_vehicle.get('grade_name', f'级配{matched_vehicle["grade_id"]}')
                send_match_message_to_vehicle(matched_vehicle['id'], car['id'], grade_name)

                going_vehicles.remove(matched_vehicle)
            else:
                print(f"[MATCH-WAITING] {car_id}号缆机(级配{car['grade_id']}) 等待同级配车辆...")

        db.commit()
        db.close()

    except Exception as e:
        print(f"[MATCH] auto match error: {e}")
        import traceback
        traceback.print_exc()


def auto_complete():
    """自动完成任务 - 兜底机制（OR逻辑：缆机送料 或 车辆返程）"""
    try:
        db = get_db()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        tasks_by_vehicle = [dict(r) for r in db.execute(
            '''SELECT t.id, t.cable_car_id, t.vehicle_id, v.tid as vehicle_tid, v.direction as vehicle_direction
               FROM dispatch_tasks t
               JOIN vehicles v ON t.vehicle_id = v.id
               WHERE t.status = 'assigned' AND v.direction = 'returning' '''
        ).fetchall()]

        for task in tasks_by_vehicle:
            db.execute('UPDATE dispatch_tasks SET status = ?, completed_at = ? WHERE id = ?',
                       ('completed', now, task['id']))
            db.execute('UPDATE cable_cars SET status = ?, grade_id = 0 WHERE id = ?',
                       ('idle', task['cable_car_id']))
            db.execute('UPDATE vehicles SET status = ?, grade_id = 0 WHERE id = ?',
                       ('idle', task['vehicle_id']))
            print(f"[COMPLETE-FALLBACK-VEHICLE] 任务#{task['id']} 已自动完成 (车辆{task['vehicle_tid']}已返程)")

        tasks_by_cable = [dict(r) for r in db.execute(
            '''SELECT t.id, t.cable_car_id, t.vehicle_id, cc.state as cable_state
               FROM dispatch_tasks t
               JOIN cable_cars cc ON t.cable_car_id = cc.id
               WHERE t.status = 'assigned' AND cc.state = 'delivering' '''
        ).fetchall()]

        for task in tasks_by_cable:
            already_completed = db.execute(
                'SELECT id FROM dispatch_tasks WHERE id = ? AND status = ?',
                (task['id'], 'completed')
            ).fetchone()
            if already_completed:
                continue

            db.execute('UPDATE dispatch_tasks SET status = ?, completed_at = ? WHERE id = ?',
                       ('completed', now, task['id']))
            db.execute('UPDATE cable_cars SET status = ?, grade_id = 0 WHERE id = ?',
                       ('idle', task['cable_car_id']))
            db.execute('UPDATE vehicles SET status = ?, grade_id = 0 WHERE id = ?',
                       ('idle', task['vehicle_id']))
            print(f"[COMPLETE-FALLBACK-CABLE] 任务#{task['id']} 已自动完成 (缆机{task['cable_car_id']}正在送料)")

        db.commit()
        db.close()
    except Exception as e:
        print(f"[COMPLETE] auto complete error: {e}")


def sync_all():
    """执行所有同步操作"""
    r1 = sync_cable_cars()
    r2 = sync_vehicles()
    if r1 and r2:
        auto_match()
        auto_complete()
    return r1 and r2


_sync_thread = None
_sync_running = False


def start_sync_loop():
    global _sync_thread, _sync_running
    if _sync_running:
        return
    _sync_running = True

    def _loop():
        while _sync_running:
            try:
                sync_all()
            except Exception as e:
                print(f"[SYNC] loop error: {e}")
            time.sleep(SYNC_INTERVAL)

    _sync_thread = threading.Thread(target=_loop, daemon=True)
    _sync_thread.start()


def stop_sync_loop():
    global _sync_running
    _sync_running = False
