#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
追踪车辆状态变化
持续监控数据库中车辆状态的变化
"""

import sqlite3
import time
from datetime import datetime

DB_PATH = 'dispatch_center/dispatch.db'

def get_vehicle_states():
    """获取当前所有车辆状态"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    rows = cursor.execute('''
        SELECT tid, name, state, state_label, direction, status, result_y, speed 
        FROM vehicles ORDER BY tid
    ''').fetchall()
    conn.close()
    return {row[0]: {
        'name': row[1], 'state': row[2], 'state_label': row[3],
        'direction': row[4], 'status': row[5], 'y': row[6], 'speed': row[7]
    } for row in rows}

def monitor():
    """持续监控状态变化"""
    prev_states = get_vehicle_states()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始监控车辆状态变化...")
    print(f"初始状态: {len(prev_states)}辆车")
    
    while True:
        time.sleep(2)
        curr_states = get_vehicle_states()
        
        changes = []
        for tid, curr in curr_states.items():
            if tid not in prev_states:
                changes.append(f"新增车辆 {curr['name']}: state={curr['state']}")
            elif prev_states[tid]['state'] != curr['state']:
                prev = prev_states[tid]
                changes.append(
                    f"{curr['name']}: {prev['state']}→{curr['state']} "
                    f"(direction: {prev['direction']}→{curr['direction']}, "
                    f"Y: {prev['y']:.0f}→{curr['y']:.0f})"
                )
        
        if changes:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 状态变化:")
            for c in changes:
                print(f"  {c}")
        
        # 检查是否全部变成delivering
        delivering_count = sum(1 for v in curr_states.values() if v['state'] == 'delivering')
        if delivering_count == len(curr_states) and delivering_count > 0:
            print(f"\n⚠️ 【警告】全部{delivering_count}辆车都变成delivering状态！")
        
        prev_states = curr_states

if __name__ == '__main__':
    try:
        monitor()
    except KeyboardInterrupt:
        print("\n监控停止")
