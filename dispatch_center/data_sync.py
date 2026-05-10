#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据同步模块 - 基于双队列的智能匹配逻辑

=== 匹配队列机制 ===

缆机等待队列（cable_car_queue）：
- 入队：缆机 returning → loading（到达装料区等待接料）
- 出队：匹配成功 / loading → delivering（已接完料出发）/ 状态异常

车辆等待队列（vehicle_queue）：
- 入队：车辆 direction='going' 且 grade_id>0 且未分配
- 优先级升级：车辆到达平台等待时升级为 at_platform
- 出队：匹配成功 / direction='returning'（已卸完料返程）/ grade_id=0 / 被分配

=== 匹配算法（FIFO + 优先级）===
1. 缆机队列按入队时间排序（先到先服务）
2. 对每台缆机，在车辆队列中找级配匹配的车辆
3. 车辆按 优先级(at_platform优先) → 入队时间(FIFO) 排序
4. 匹配第一个，双方出队

=== 任务完成逻辑（OR逻辑）===
触发源1: 缆机 loading → delivering（缆机开始送料）
触发源2: 车辆 going → returning（车辆开始返程）
兜底机制: auto_complete() 定期检查当前状态
"""

import pymysql
import sqlite3
import threading
import time
from collections import deque
from datetime import datetime
from config import CABLE_CAR_DB, VEHICLE_DB, SYNC_INTERVAL, VEHICLE_GOING_THRESHOLD, DB_PATH
from database import get_db
from state_detector import (
    detect_cable_car_state,
    detect_vehicle_state_locked,
    force_unlock_vehicle_state,
    get_vehicle_locked_state,
    LOADING_ZONE, UNLOADING_ZONE,
    VEHICLE_LOADING_ZONE, VEHICLE_UNLOADING_ZONE, VEHICLE_DELIVERING_ZONE,
    VEHICLE_Y_DELTA_THRESHOLD
)

VEHICLE_Y_HISTORY_SIZE = 5
VEHICLE_DIRECTION_CONFIRM_FRAMES = 2

PRIORITY_AT_PLATFORM = 0
PRIORITY_ON_THE_WAY = 1

_vehicle_y_history = {}
_vehicle_prev_direction = {}
_vehicle_direction_confirm = {}

_cable_car_prev_state = {}

_cable_car_queue = []
_vehicle_queue = []

CABLE_CAR_COOLDOWN = 180
VEHICLE_COOLDOWN = 300
_cable_car_cooldown = {}
_vehicle_cooldown = {}


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
    """检测车辆行驶方向 - 配合状态锁定机制"""
    global _vehicle_y_history, _vehicle_prev_direction, _vehicle_direction_confirm

    if tid not in _vehicle_y_history:
        _vehicle_y_history[tid] = deque(maxlen=VEHICLE_Y_HISTORY_SIZE)

    history = _vehicle_y_history[tid]
    history.append(result_y)

    # 获取当前锁定状态
    locked_state = get_vehicle_locked_state(tid)

    if speed is None or float(speed) < 0.1:
        # 车辆几乎停止
        # 如果状态锁定在delivering/returning，保留方向信息（配合状态锁定）
        # 只有在standby/unloading_wait等稳定状态下才清除方向
        if locked_state in ('delivering', 'returning'):
            prev_dir = _vehicle_prev_direction.get(tid, 'idle')
            if prev_dir in ('going', 'returning'):
                return prev_dir
        # 其他状态：清除方向
        prev_dir = _vehicle_prev_direction.get(tid, 'idle')
        if prev_dir in ('going', 'returning'):
            _vehicle_prev_direction[tid] = 'idle'
            for key in list(_vehicle_direction_confirm.keys()):
                if isinstance(key, str) and key.startswith(f"{tid}_"):
                    del _vehicle_direction_confirm[key]
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
    history = _vehicle_y_history.get(tid)
    if not history or len(history) < 2:
        return 0
    hist_list = list(history)
    trend = 0
    for i in range(1, len(hist_list)):
        trend += hist_list[i] - hist_list[i - 1]
    return trend


def _cable_car_queue_enter(car_id, grade_id, now):
    global _cable_car_queue
    for item in _cable_car_queue:
        if item['car_id'] == car_id:
            if item['grade_id'] != grade_id:
                item['grade_id'] = grade_id
                print(f"[QUEUE-CABLE-UPDATE] {car_id}号缆机级配更新为{grade_id}")
            return
    _cable_car_queue.append({
        'car_id': car_id,
        'grade_id': grade_id,
        'enter_time': now
    })
    print(f"[QUEUE-CABLE-IN] {car_id}号缆机入队(级配={grade_id}), 队列长度={len(_cable_car_queue)}")


def _cable_car_queue_exit(car_id, reason=''):
    global _cable_car_queue
    before = len(_cable_car_queue)
    _cable_car_queue = [item for item in _cable_car_queue if item['car_id'] != car_id]
    if len(_cable_car_queue) < before:
        print(f"[QUEUE-CABLE-OUT] {car_id}号缆机出队({reason}), 队列长度={len(_cable_car_queue)}")


def _vehicle_queue_enter(vehicle_id, tid, grade_id, now, at_platform=False):
    global _vehicle_queue
    for item in _vehicle_queue:
        if item['vehicle_id'] == vehicle_id:
            if at_platform and item['priority'] != PRIORITY_AT_PLATFORM:
                item['priority'] = PRIORITY_AT_PLATFORM
                print(f"[QUEUE-VEHICLE-UPGRADE] {tid}号车优先级升级为at_platform")
            if item['grade_id'] != grade_id:
                item['grade_id'] = grade_id
            return
    priority = PRIORITY_AT_PLATFORM if at_platform else PRIORITY_ON_THE_WAY
    _vehicle_queue.append({
        'vehicle_id': vehicle_id,
        'tid': tid,
        'grade_id': grade_id,
        'enter_time': now,
        'priority': priority
    })
    p_label = 'at_platform' if at_platform else 'on_the_way'
    print(f"[QUEUE-VEHICLE-IN] {tid}号车入队(级配={grade_id}, 优先级={p_label}), 队列长度={len(_vehicle_queue)}")


def _vehicle_queue_exit(vehicle_id, reason=''):
    global _vehicle_queue
    before = len(_vehicle_queue)
    _vehicle_queue = [item for item in _vehicle_queue if item['vehicle_id'] != vehicle_id]
    if len(_vehicle_queue) < before:
        print(f"[QUEUE-VEHICLE-OUT] 车辆{vehicle_id}出队({reason}), 队列长度={len(_vehicle_queue)}")


def _is_cable_car_cooling(car_id):
    if car_id not in _cable_car_cooldown:
        return False
    if datetime.now().timestamp() >= _cable_car_cooldown[car_id]:
        del _cable_car_cooldown[car_id]
        return False
    return True


def _is_vehicle_cooling(vehicle_id):
    if vehicle_id not in _vehicle_cooldown:
        return False
    if datetime.now().timestamp() >= _vehicle_cooldown[vehicle_id]:
        del _vehicle_cooldown[vehicle_id]
        return False
    return True


def get_cable_car_cooldown_remaining(car_id):
    if car_id not in _cable_car_cooldown:
        return 0
    remaining = int(_cable_car_cooldown[car_id] - datetime.now().timestamp())
    if remaining <= 0:
        del _cable_car_cooldown[car_id]
        return 0
    return remaining


def get_vehicle_cooldown_remaining(vehicle_id):
    if vehicle_id not in _vehicle_cooldown:
        return 0
    remaining = int(_vehicle_cooldown[vehicle_id] - datetime.now().timestamp())
    if remaining <= 0:
        del _vehicle_cooldown[vehicle_id]
        return 0
    return remaining


def _try_complete_task_by_cable_car(car_id, local_db, now):
    """缆机开始送料 → OR逻辑直接完成任务"""
    task = local_db.execute(
        '''SELECT t.id, t.vehicle_id, v.tid as vehicle_tid
           FROM dispatch_tasks t
           JOIN vehicles v ON t.vehicle_id = v.id
           WHERE t.cable_car_id = ? AND t.status = 'assigned'
           LIMIT 1''',
        (car_id,)
    ).fetchone()

    if task:
        _do_complete_task(task, local_db, now, '缆机送料')
        return True
    return False


def _try_complete_task_by_vehicle(vehicle_id, local_db, now):
    """车辆返程 → OR逻辑直接完成任务"""
    task = local_db.execute(
        '''SELECT t.id, t.cable_car_id, t.vehicle_id, v.tid as vehicle_tid
           FROM dispatch_tasks t
           JOIN vehicles v ON t.vehicle_id = v.id
           WHERE t.vehicle_id = ? AND t.status = 'assigned'
           LIMIT 1''',
        (vehicle_id,)
    ).fetchone()

    if task:
        _do_complete_task(task, local_db, now, '车辆返程')
        return True
    return False


def _do_complete_task(task, local_db, now, reason=''):
    """执行任务完成操作 + 设置冷却时间"""
    already = local_db.execute('SELECT status FROM dispatch_tasks WHERE id = ?', (task['id'],)).fetchone()
    if already and already['status'] == 'completed':
        return

    local_db.execute('UPDATE dispatch_tasks SET status = ?, completed_at = ? WHERE id = ?',
                     ('completed', now, task['id']))
    local_db.execute('UPDATE cable_cars SET status = ? WHERE id = ?',
                     ('idle', task['cable_car_id']))
    local_db.execute('UPDATE vehicles SET status = ? WHERE id = ?',
                     ('idle', task['vehicle_id']))
    _cable_car_queue_exit(task['cable_car_id'], f'任务完成-{reason}')
    _vehicle_queue_exit(task['vehicle_id'], f'任务完成-{reason}')
    _update_vehicle_unloading_port(task['vehicle_tid'], None, action='clear')

    now_ts = datetime.now().timestamp()
    _cable_car_cooldown[task['cable_car_id']] = now_ts + CABLE_CAR_COOLDOWN
    _vehicle_cooldown[task['vehicle_id']] = now_ts + VEHICLE_COOLDOWN

    print(f"[COMPLETE] 任务#{task['id']} 已完成({reason}) | "
          f"缆机{task['cable_car_id']}冷却{CABLE_CAR_COOLDOWN}s, "
          f"车辆{task['vehicle_id']}冷却{VEHICLE_COOLDOWN}s")


def sync_cable_cars():
    """同步缆机数据并检测状态切换 + 管理缆机等待队列"""
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

        local_db = sqlite3.connect(DB_PATH, timeout=10)
        local_db.row_factory = sqlite3.Row
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

                # 缆机入队：仅在 returning → loading 切换时入队
                # 这是唯一正确的入队时机，表示缆机刚回到装料区准备接料
                if prev_state == 'returning' and state == 'loading':
                    active_task = local_db.execute(
                        'SELECT id FROM dispatch_tasks WHERE cable_car_id = ? AND status = ?',
                        (car_id, 'assigned')
                    ).fetchone()
                    if active_task:
                        print(f"[QUEUE-SKIP] {car_id}号缆机有未完成任务，跳过入队")
                    elif _is_cable_car_cooling(car_id):
                        remaining = int(_cable_car_cooldown[car_id] - datetime.now().timestamp())
                        print(f"[QUEUE-COOLDOWN] {car_id}号缆机冷却中，剩余{remaining}s")
                    else:
                        current = local_db.execute('SELECT grade_id FROM cable_cars WHERE id = ?', (car_id,)).fetchone()
                        grade_id = current['grade_id'] if current else 0
                        _cable_car_queue_enter(car_id, grade_id, now)

                # 缆机出队+确认：loading → delivering（缆机开始送料）
                if prev_state == 'loading' and state == 'delivering':
                    _cable_car_queue_exit(car_id, '开始送料')
                    _try_complete_task_by_cable_car(car_id, local_db, now)

                # 其他状态变化时，如果还在队列中则出队
                if state not in ('loading',) and any(item['car_id'] == car_id for item in _cable_car_queue):
                    _cable_car_queue_exit(car_id, f'状态变为{state}')

            _cable_car_prev_state[car_id] = state

            current = local_db.execute('SELECT status, grade_id FROM cable_cars WHERE id = ?', (car_id,)).fetchone()
            if current and current['status'] == 'assigned':
                local_db.execute('''UPDATE cable_cars SET latitude=?, longitude=?, altitude=?,
                    xspeed=?, yspeed=?, start=?, state=?, state_label=?, location=?, direction=?, updated_at=?, synced_at=?
                    WHERE id=?''',
                    (latitude, longitude, altitude, xspeed, yspeed, start,
                     state, state_label, location, direction, updated_at, now, car_id))
            else:
                in_queue = any(item['car_id'] == car_id for item in _cable_car_queue)
                if in_queue:
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
    """同步车辆数据 - 增强版（状态识别 + 队列管理 + 任务完成触发）"""
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

        local_db = sqlite3.connect(DB_PATH, timeout=10)
        local_db.row_factory = sqlite3.Row
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
            v_state, v_state_label, v_location = detect_vehicle_state_locked(tid, result_y, speed, y_trend, direction)

            if prev_direction in ('going', 'idle') and direction == 'returning':
                print(f"[VEHICLE-STATE] {tid}号车方向切换: {prev_direction} → returning")

            existing = local_db.execute('SELECT id, status, direction, grade_id FROM vehicles WHERE tid = ?', (tid,)).fetchone()
            if existing:
                vehicle_id = existing['id']
                old_direction = existing['direction']
                grade_id = existing['grade_id']

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
                        _vehicle_queue_exit(vehicle_id, '已返程')
                else:
                    new_status = 'going' if direction == 'going' else 'idle'
                    local_db.execute('''UPDATE vehicles SET result_x=?, result_y=?, speed=?, lat=?, lon=?,
                        user_name=?, route=?, direction=?, status=?, state=?, state_label=?, location=?,
                        updated_at=?, synced_at=?
                        WHERE tid=?''',
                        (result_x, result_y, speed, lat, lon, user_name, route, direction,
                         new_status, v_state, v_state_label, v_location,
                         updated_at, now, tid))

                    if direction == 'going' and grade_id > 0:
                        if _is_vehicle_cooling(vehicle_id):
                            remaining = int(_vehicle_cooldown[vehicle_id] - datetime.now().timestamp())
                            print(f"[QUEUE-COOLDOWN] {tid}号车冷却中，剩余{remaining}s")
                        else:
                            at_platform = result_y <= VEHICLE_UNLOADING_ZONE[1]
                            _vehicle_queue_enter(vehicle_id, tid, grade_id, now, at_platform=at_platform)
                    elif direction == 'returning':
                        _vehicle_queue_exit(vehicle_id, '已返程')
                    elif grade_id == 0:
                        _vehicle_queue_exit(vehicle_id, '级配清零')
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


def _update_vehicle_unloading_port(tid, cable_car_id, action='assign'):
    """
    更新 vehicle_system.data 表的 unloading_port 字段

    Args:
        tid: 车辆ID（datum_data.tid）
        cable_car_id: 缆机ID
        action: 'assign' 分配缆机 / 'clear' 清空缆机
    """
    try:
        conn = _get_vehicle_conn()
        cursor = conn.cursor()

        if action == 'assign':
            cursor.execute(
                'UPDATE data SET unloading_port = %s WHERE tid = %s',
                (cable_car_id, tid)
            )
            if cursor.rowcount > 0:
                print(f"[DB-WRITE] 车辆{tid}的unloading_port设置为{cable_car_id}号缆机")
            else:
                print(f"[DB-WRITE-WARN] 车辆{tid}在data表中不存在，无法更新unloading_port")
        else:  # clear
            # 注意：unloading_port 字段是 NOT NULL，用 0 表示清空/未分配
            cursor.execute(
                'UPDATE data SET unloading_port = 0 WHERE tid = %s',
                (tid,)
            )
            if cursor.rowcount > 0:
                print(f"[DB-WRITE] 车辆{tid}的unloading_port已清空(设置为0)")

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB-WRITE-ERROR] 更新vehicle_system.data失败: {e}")
        return False


def _cleanup_queues(db):
    """清理队列中的无效条目"""
    global _cable_car_queue, _vehicle_queue

    valid_cars = set()
    for row in db.execute('SELECT id FROM cable_cars').fetchall():
        valid_cars.add(row['id'])

    before = len(_cable_car_queue)
    _cable_car_queue = [item for item in _cable_car_queue if item['car_id'] in valid_cars]
    if len(_cable_car_queue) < before:
        print(f"[QUEUE-CLEANUP] 缆机队列清理: {before} → {len(_cable_car_queue)}")

    for item in _cable_car_queue:
        car = db.execute('SELECT grade_id, status, state FROM cable_cars WHERE id = ?',
                         (item['car_id'],)).fetchone()
        if car:
            item['grade_id'] = car['grade_id']
            if car['status'] == 'assigned':
                _cable_car_queue = [q for q in _cable_car_queue if q['car_id'] != item['car_id']]
                print(f"[QUEUE-CLEANUP] {item['car_id']}号缆机已分配，移出队列")
            elif car['state'] not in ('loading',):
                _cable_car_queue = [q for q in _cable_car_queue if q['car_id'] != item['car_id']]
                print(f"[QUEUE-CLEANUP] {item['car_id']}号缆机状态非loading，移出队列")

    valid_vehicles = set()
    for row in db.execute('SELECT id FROM vehicles').fetchall():
        valid_vehicles.add(row['id'])

    before = len(_vehicle_queue)
    _vehicle_queue = [item for item in _vehicle_queue if item['vehicle_id'] in valid_vehicles]
    if len(_vehicle_queue) < before:
        print(f"[QUEUE-CLEANUP] 车辆队列清理: {before} → {len(_vehicle_queue)}")

    for item in _vehicle_queue:
        v = db.execute('SELECT grade_id, status, direction, state, result_y FROM vehicles WHERE id = ?',
                       (item['vehicle_id'],)).fetchone()
        if v:
            item['grade_id'] = v['grade_id']
            if v['status'] == 'assigned':
                _vehicle_queue = [q for q in _vehicle_queue if q['vehicle_id'] != item['vehicle_id']]
                print(f"[QUEUE-CLEANUP] 车辆{item['tid']}已分配，移出队列")
            elif v['direction'] == 'returning':
                _vehicle_queue = [q for q in _vehicle_queue if q['vehicle_id'] != item['vehicle_id']]
                print(f"[QUEUE-CLEANUP] 车辆{item['tid']}已返程，移出队列")
            elif v['grade_id'] == 0:
                _vehicle_queue = [q for q in _vehicle_queue if q['vehicle_id'] != item['vehicle_id']]
                print(f"[QUEUE-CLEANUP] 车辆{item['tid']}级配清零，移出队列")
            elif v['result_y'] <= VEHICLE_UNLOADING_ZONE[1]:  # Y <= -950，到达卸料区
                if item['priority'] != PRIORITY_AT_PLATFORM:
                    item['priority'] = PRIORITY_AT_PLATFORM
                    print(f"[QUEUE-VEHICLE-UPGRADE] {item['tid']}号车到达卸料区(Y={v['result_y']:.0f})，优先级升级")


def auto_match():
    """自动匹配逻辑 - FIFO + 优先级队列匹配"""
    global _cable_car_queue, _vehicle_queue

    try:
        db = sqlite3.connect(DB_PATH, timeout=10)
        db.row_factory = sqlite3.Row
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        _cleanup_queues(db)

        if not _cable_car_queue:
            db.close()
            return

        _cable_car_queue.sort(key=lambda x: x['enter_time'])

        if not _vehicle_queue:
            waiting_info = ', '.join([f"{item['car_id']}号(级配{item['grade_id']})" for item in _cable_car_queue])
            print(f"[MATCH] {len(_cable_car_queue)}台缆机等待中: {waiting_info}, 暂无可用车辆")
            db.close()
            return

        _vehicle_queue.sort(key=lambda x: (x['priority'], x['enter_time']))

        print(f"[MATCH] 缆机队列={len(_cable_car_queue)}, 车辆队列={len(_vehicle_queue)}")

        matched_vehicle_ids = set()

        for car_item in list(_cable_car_queue):
            car_id = car_item['car_id']
            car = db.execute('SELECT * FROM cable_cars WHERE id = ?', (car_id,)).fetchone()
            if not car:
                continue

            car_grade = car['grade_id']
            if car_grade == 0:
                print(f"[MATCH] {car_id}号缆机未设置级配，跳过")
                continue

            if car['status'] == 'assigned':
                _cable_car_queue = [q for q in _cable_car_queue if q['car_id'] != car_id]
                continue

            best_vehicle = None
            best_vehicle_item = None
            for v_item in _vehicle_queue:
                if v_item['vehicle_id'] in matched_vehicle_ids:
                    continue
                if v_item['grade_id'] == car_grade:
                    best_vehicle_item = v_item
                    v = db.execute('SELECT * FROM vehicles WHERE id = ?', (v_item['vehicle_id'],)).fetchone()
                    if v:
                        best_vehicle = dict(v)
                    break

            if best_vehicle and best_vehicle_item:
                grade_names = {1: '二级配', 2: '三级配', 3: '四级配', 4: '三级配PVA纤维', 5: '三级富浆'}
                grade_name = grade_names.get(car_grade, f'级配{car_grade}')
                p_label = '平台等待' if best_vehicle_item['priority'] == PRIORITY_AT_PLATFORM else '路上'

                print(f"[MATCH-FIFO] {car_id}号缆机 ↔ {best_vehicle['name']} 匹配成功 "
                      f"({grade_name}, 车辆{p_label}, 缆机等待时长={_wait_seconds(car_item['enter_time'])}s)")

                db.execute(
                    'INSERT INTO dispatch_tasks (cable_car_id, vehicle_id, grade_id, status, created_at, assigned_at) VALUES (?, ?, ?, ?, ?, ?)',
                    (car['id'], best_vehicle['id'], car_grade, 'assigned', now, now)
                )

                db.execute('UPDATE cable_cars SET status = ? WHERE id = ?', ('assigned', car['id']))
                db.execute('UPDATE vehicles SET status = ? WHERE id = ?', ('assigned', best_vehicle['id']))

                _cable_car_queue = [q for q in _cable_car_queue if q['car_id'] != car_id]
                matched_vehicle_ids.add(best_vehicle_item['vehicle_id'])

                send_match_message_to_vehicle(best_vehicle['id'], car['id'], grade_name)

                _update_vehicle_unloading_port(best_vehicle_item['tid'], car['id'], action='assign')
            else:
                print(f"[MATCH-WAITING] {car_id}号缆机(级配{car_grade}) 等待同级配车辆...")

        _vehicle_queue = [item for item in _vehicle_queue if item['vehicle_id'] not in matched_vehicle_ids]

        db.commit()
        db.close()

    except Exception as e:
        print(f"[MATCH] auto match error: {e}")
        import traceback
        traceback.print_exc()


def _wait_seconds(enter_time_str):
    try:
        enter_time = datetime.strptime(enter_time_str, '%Y-%m-%d %H:%M:%S')
        delta = (datetime.now() - enter_time).total_seconds()
        return int(delta)
    except:
        return 0


def auto_complete():
    """自动完成任务 - OR逻辑（缆机送料 或 车辆返程，任一即完成）"""
    try:
        db = sqlite3.connect(DB_PATH, timeout=10)
        db.row_factory = sqlite3.Row
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 条件1：车辆返程 → 完成
        tasks_by_vehicle = [dict(r) for r in db.execute(
            '''SELECT t.id, t.cable_car_id, t.vehicle_id, v.tid as vehicle_tid
               FROM dispatch_tasks t
               JOIN vehicles v ON t.vehicle_id = v.id
               WHERE t.status = 'assigned' AND v.direction = 'returning' '''
        ).fetchall()]

        for task in tasks_by_vehicle:
            _do_complete_task(task, db, now, '车辆返程')

        # 条件2：缆机送料 → 完成
        tasks_by_cable = [dict(r) for r in db.execute(
            '''SELECT t.id, t.cable_car_id, t.vehicle_id, v.tid as vehicle_tid
               FROM dispatch_tasks t
               JOIN vehicles v ON t.vehicle_id = v.id
               JOIN cable_cars cc ON t.cable_car_id = cc.id
               WHERE t.status = 'assigned' AND cc.state = 'delivering' '''
        ).fetchall()]

        for task in tasks_by_cable:
            already = db.execute(
                'SELECT id FROM dispatch_tasks WHERE id = ? AND status = ?',
                (task['id'], 'completed')
            ).fetchone()
            if not already:
                _do_complete_task(task, db, now, '缆机送料')

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
