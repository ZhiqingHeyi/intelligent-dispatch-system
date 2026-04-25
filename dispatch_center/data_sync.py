#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据同步模块 - 包含基于状态切换的智能匹配逻辑

匹配触发逻辑：
1. 缆机从 "返程途中(returning)" → "990平台接料(loading)" 触发匹配
2. 在接料期间持续寻找同级别送料车辆
3. 缆机从 "990平台接料(loading)" → "送料途中(delivering)" 结束匹配

状态流转：
返程途中 → 990平台接料 → 送料途中
    ↓           ↓              ↓
(卸完料)   (触发匹配)      (结束匹配)
"""

import pymysql
import threading
import time
from datetime import datetime
from config import CABLE_CAR_DB, VEHICLE_DB, SYNC_INTERVAL, VEHICLE_GOING_THRESHOLD
from database import get_db
from state_detector import detect_cable_car_state, LOADING_ZONE, UNLOADING_ZONE

# 车辆Y坐标历史记录（用于判断车辆方向）
_vehicle_prev_y = {}

# 缆机状态历史记录（用于检测状态切换）
_cable_car_prev_state = {}

# 正在匹配中的缆机（记录缆机ID和匹配开始时间）
_matching_cable_cars = {}


def _get_cable_car_conn():
    return pymysql.connect(**CABLE_CAR_DB)


def _get_vehicle_conn():
    return pymysql.connect(**VEHICLE_DB)


def detect_cable_car_direction(xspeed, start):
    """兼容旧接口，实际使用detect_cable_car_state
    
    速度方向说明：
    - xspeed > 0（正值）：X增加，向卸料区移动 → going（送料）
    - xspeed < 0（负值）：X减小，向装料区移动 → returning（返程）
    """
    if start == 0:
        return 'stopped'
    if xspeed > 0.5:
        # X增加，向卸料区 → 送料
        return 'going'
    if xspeed < -0.5:
        # X减小，向装料区 → 返程
        return 'returning'
    return 'idle'


def detect_vehicle_direction(tid, result_y, speed):
    """检测车辆行驶方向"""
    global _vehicle_prev_y
    if speed is None or float(speed) < 0.1:
        return 'stopped'
    prev_y = _vehicle_prev_y.get(tid)
    _vehicle_prev_y[tid] = result_y
    if prev_y is None:
        return 'idle'
    delta_y = result_y - prev_y
    if delta_y < VEHICLE_GOING_THRESHOLD:
        return 'going'
    if delta_y > abs(VEHICLE_GOING_THRESHOLD):
        return 'returning'
    return 'idle'


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

            # 使用新的状态检测 - 基于位置+速度
            state, state_label, location = detect_cable_car_state(latitude, xspeed, start)
            
            # 兼容旧版direction字段
            direction = detect_cable_car_direction(xspeed, start)
            
            # 检测状态切换
            prev_state = _cable_car_prev_state.get(car_id)
            
            # 状态切换检测
            if prev_state and prev_state != state:
                print(f"[STATE] {car_id}号缆机状态切换: {prev_state} → {state}")
                
                # 触发匹配：返程途中 → 990平台接料
                if prev_state == 'returning' and state == 'loading':
                    print(f"[MATCH-TRIGGER] {car_id}号缆机到达装料区，开始匹配车辆")
                    _matching_cable_cars[car_id] = {
                        'start_time': now,
                        'matched': False,
                        'vehicle_id': None
                    }
                
                # 结束匹配：990平台接料 → 送料途中
                if prev_state == 'loading' and state == 'delivering':
                    if car_id in _matching_cable_cars:
                        match_info = _matching_cable_cars.pop(car_id)
                        if match_info['matched']:
                            print(f"[MATCH-END] {car_id}号缆机开始送料，匹配任务继续执行")
                        else:
                            print(f"[MATCH-END] {car_id}号缆机开始送料，未匹配到车辆（可能已人工调度）")
            
            # 更新状态记录
            _cable_car_prev_state[car_id] = state

            # 更新数据库
            current = local_db.execute('SELECT status, grade_id FROM cable_cars WHERE id = ?', (car_id,)).fetchone()
            if current and current['status'] == 'assigned':
                # 已分配任务的保持状态
                local_db.execute('''UPDATE cable_cars SET latitude=?, longitude=?, altitude=?, 
                    xspeed=?, yspeed=?, start=?, state=?, state_label=?, location=?, direction=?, updated_at=?, synced_at=?
                    WHERE id=?''',
                    (latitude, longitude, altitude, xspeed, yspeed, start, 
                     state, state_label, location, direction, updated_at, now, car_id))
            else:
                # 检查是否在匹配中
                if car_id in _matching_cable_cars and not _matching_cable_cars[car_id]['matched']:
                    new_status = 'matching'  # 匹配中状态
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
    """同步车辆数据"""
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

            direction = detect_vehicle_direction(tid, result_y, speed)

            existing = local_db.execute('SELECT id, status FROM vehicles WHERE tid = ?', (tid,)).fetchone()
            if existing:
                vehicle_id = existing['id']
                if existing['status'] == 'assigned':
                    local_db.execute('''UPDATE vehicles SET result_x=?, result_y=?, speed=?, lat=?, lon=?,
                        user_name=?, route=?, direction=?, updated_at=?, synced_at=?
                        WHERE tid=?''',
                        (result_x, result_y, speed, lat, lon, user_name, route, direction, updated_at, now, tid))
                else:
                    new_status = 'going' if direction == 'going' else 'idle'
                    local_db.execute('''UPDATE vehicles SET result_x=?, result_y=?, speed=?, lat=?, lon=?,
                        user_name=?, route=?, direction=?, status=?, updated_at=?, synced_at=?
                        WHERE tid=?''',
                        (result_x, result_y, speed, lat, lon, user_name, route, direction,
                         new_status, updated_at, now, tid))
            else:
                new_status = 'going' if direction == 'going' else 'idle'
                local_db.execute('''INSERT INTO vehicles (tid, name, grade_id, status, direction, result_x, result_y,
                    speed, lat, lon, user_name, route, updated_at, synced_at)
                    VALUES (?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (tid, user_name or f'{tid}号车',
                     new_status, direction,
                     result_x, result_y, speed, lat, lon, user_name, route, updated_at, now))
        
        local_db.commit()
        local_db.close()
        return True
    except Exception as e:
        print(f"[SYNC] vehicle sync error: {e}")
        return False


def send_match_message_to_vehicle(vehicle_id, cable_car_id, grade_name):
    """
    发送匹配成功消息给车辆
    
    预留接口：后续实现消息推送功能
    
    Args:
        vehicle_id: 车辆ID
        cable_car_id: 缆机ID
        grade_name: 级配名称
    """
    # TODO: 实现消息推送逻辑
    # 可能的方式：
    # 1. 调用车辆系统的API
    # 2. 写入消息队列
    # 3. WebSocket推送
    print(f"[MSG-RESERVE] 向车辆{vehicle_id}发送消息: 请前往{cable_car_id}号缆机({grade_name})")
    return True


def auto_match():
    """
    自动匹配逻辑
    
    匹配条件：
    1. 缆机在_matching_cable_cars列表中（已从返程切换到接料状态）
    2. 缆机尚未匹配成功
    3. 缆机已设置级配(grade_id > 0)
    4. 寻找同级别且正在送料的车辆
    """
    global _matching_cable_cars
    
    try:
        db = get_db()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取正在匹配中的缆机
        matching_car_ids = [car_id for car_id, info in _matching_cable_cars.items() 
                           if not info['matched']]
        
        if not matching_car_ids:
            db.close()
            return
        
        print(f"[MATCH] 当前有{len(matching_car_ids)}台缆机正在匹配中: {matching_car_ids}")
        
        # 获取这些缆机的详细信息
        cars = []
        for car_id in matching_car_ids:
            car = db.execute('SELECT * FROM cable_cars WHERE id = ?', (car_id,)).fetchone()
            if car:
                cars.append(dict(car))
        
        # 获取可用的送料车辆（going状态 + 已设置级配 + 未被分配）
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
        
        # 执行匹配
        for car in cars:
            car_id = car['id']
            
            # 检查是否已设置级配
            if car['grade_id'] == 0:
                print(f"[MATCH] {car_id}号缆机未设置级配，跳过匹配")
                continue
            
            # 寻找同级别车辆
            matched_vehicle = None
            for v in going_vehicles:
                if v['grade_id'] == car['grade_id']:
                    matched_vehicle = v
                    break
            
            if matched_vehicle:
                # 匹配成功，创建任务
                print(f"[MATCH-SUCCESS] {car_id}号缆机({car.get('grade_name', '未知级配')}) ↔ {matched_vehicle['name']} 匹配成功")
                
                # 创建调度任务
                db.execute(
                    'INSERT INTO dispatch_tasks (cable_car_id, vehicle_id, grade_id, status, created_at, assigned_at) VALUES (?, ?, ?, ?, ?, ?)',
                    (car['id'], matched_vehicle['id'], car['grade_id'], 'assigned', now, now)
                )
                
                # 更新缆机和车辆状态
                db.execute('UPDATE cable_cars SET status = ? WHERE id = ?', ('assigned', car['id']))
                db.execute('UPDATE vehicles SET status = ? WHERE id = ?', ('assigned', matched_vehicle['id']))
                
                # 标记为已匹配
                _matching_cable_cars[car_id]['matched'] = True
                _matching_cable_cars[car_id]['vehicle_id'] = matched_vehicle['id']
                
                # 预留：发送消息给车辆
                grade_name = matched_vehicle.get('grade_name', f'级配{matched_vehicle["grade_id"]}')
                send_match_message_to_vehicle(matched_vehicle['id'], car['id'], grade_name)
                
                # 从未匹配车辆列表中移除
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
    """自动完成任务 - 当车辆返程时完成任务"""
    try:
        db = get_db()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        assigned_tasks = [dict(r) for r in db.execute(
            '''SELECT t.*, v.direction as vehicle_direction, v.tid as vehicle_tid
               FROM dispatch_tasks t
               JOIN vehicles v ON t.vehicle_id = v.id
               WHERE t.status = 'assigned' AND v.direction = 'returning' '''
        ).fetchall()]

        for task in assigned_tasks:
            db.execute('UPDATE dispatch_tasks SET status = ?, completed_at = ? WHERE id = ?',
                       ('completed', now, task['id']))
            db.execute('UPDATE cable_cars SET status = ?, grade_id = 0 WHERE id = ?',
                       ('idle', task['cable_car_id']))
            db.execute('UPDATE vehicles SET status = ?, grade_id = 0 WHERE id = ?',
                       ('idle', task['vehicle_id']))
            print(f"[COMPLETE] 任务#{task['id']} 已自动完成 (车辆{task['vehicle_tid']}已返程)")

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


# 同步线程控制
_sync_thread = None
_sync_running = False


def start_sync_loop():
    """启动同步循环"""
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
    """停止同步循环"""
    global _sync_running
    _sync_running = False
