#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
车辆状态调试工具 - 监控API返回的数据
"""

import sqlite3
import json
from datetime import datetime

DB_PATH = 'dispatch_center/dispatch.db'

def debug_vehicle_state():
    """打印当前车辆状态，用于调试"""
    print("=" * 100)
    print(f"车辆状态调试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取所有车辆数据
    rows = cursor.execute('''
        SELECT id, tid, name, status, direction, state, state_label, location, 
               result_y, speed, grade_id, updated_at
        FROM vehicles
        ORDER BY tid
    ''').fetchall()
    
    print(f"\n{'ID':<4} {'TID':<4} {'名称':<8} {'status':<10} {'direction':<10} {'state':<15} {'state_label':<10} {'location':<10} {'Y坐标':<10} {'速度':<8}")
    print("-" * 100)
    
    state_count = {}
    direction_count = {}
    
    for row in rows:
        state = row['state'] or 'NULL'
        direction = row['direction'] or 'NULL'
        state_label = row['state_label'] or 'NULL'
        
        state_count[state] = state_count.get(state, 0) + 1
        direction_count[direction] = direction_count.get(direction, 0) + 1
        
        print(f"{row['id']:<4} {row['tid']:<4} {row['name']:<8} {row['status'] or 'NULL':<10} "
              f"{direction:<10} {state:<15} {state_label:<10} {row['location'] or 'NULL':<10} "
              f"{row['result_y']:<10.1f} {row['speed']:<8.1f}")
    
    print("-" * 100)
    print(f"\n【统计】state分布: {state_count}")
    print(f"【统计】direction分布: {direction_count}")
    
    # 检查是否有问题数据
    problematic = [r for r in rows if r['state'] in ('delivering', 'going') and r['result_y'] > 50]
    if problematic:
        print(f"\n⚠️ 发现可疑数据（state=delivering/going 但 Y>50 在接料区）:")
        for r in problematic:
            print(f"   - {r['name']}: state={r['state']}, Y={r['result_y']}")
    
    conn.close()
    print("\n" + "=" * 100)

if __name__ == '__main__':
    debug_vehicle_state()
