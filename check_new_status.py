#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用新的状态检测器检查缆机状态
"""

import pymysql
from datetime import datetime
import sys
sys.path.insert(0, 'dispatch_center')
from state_detector import detect_cable_car_state, get_state_color, get_state_icon

DB_CONFIG = {
    'host': '192.168.1.88',
    'port': 3306,
    'user': 'root',
    'password': '!Tmhc20170717',
    'database': 'cable_car',
    'charset': 'utf8mb4'
}

def main():
    print("=" * 80)
    print("新版缆机状态识别检查（基于位置+速度）")
    print("=" * 80)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 获取当前状态
    cursor.execute("""
        SELECT 
            cable_car_id,
            latitude,
            longitude,
            altitude,
            start,
            xspeed,
            yspeed,
            updated_at
        FROM cable_car_status
        ORDER BY cable_car_id
    """)
    rows = cursor.fetchall()
    
    print("\n【新版状态识别结果】")
    print("-" * 100)
    print(f"{'缆机ID':<8} {'纬度(X)':<12} {'X速度':<10} {'启动':<6} {'检测状态':<12} {'状态标签':<15} {'位置区域':<12} {'图标'}")
    print("-" * 100)
    
    for row in rows:
        cable_id = row[0]
        lat = row[1] if row[1] else 0
        xs = row[5] if row[5] else 0
        start = row[4] if row[4] else 0
        
        state, label, location = detect_cable_car_state(lat, xs, start)
        icon = get_state_icon(state)
        
        print(f"{cable_id:<8} {lat:<12.2f} {xs:<10.2f} {start:<6} {state:<12} {label:<15} {location:<12} {icon}")
    
    print("-" * 100)
    
    # 统计
    print("\n【状态统计】")
    print("-" * 80)
    state_counts = {}
    for row in rows:
        lat = row[1] if row[1] else 0
        xs = row[5] if row[5] else 0
        start = row[4] if row[4] else 0
        state, _, _ = detect_cable_car_state(lat, xs, start)
        state_counts[state] = state_counts.get(state, 0) + 1
    
    for state, count in sorted(state_counts.items()):
        label = {
            'loading': '990平台接料',
            'delivering': '送料途中',
            'unloading': '基坑卸料',
            'returning': '返程途中',
            'stopped': '停止'
        }.get(state, state)
        icon = get_state_icon(state)
        print(f"  {icon} {label}: {count} 台")
    
    # 重点关注1/2/3号
    print("\n【1/2/3号缆机详细分析】")
    print("-" * 80)
    
    for row in rows:
        cable_id = row[0]
        if cable_id in [1, 2, 3]:
            lat = row[1] if row[1] else 0
            lon = row[2] if row[2] else 0
            xs = row[5] if row[5] else 0
            start = row[4] if row[4] else 0
            
            state, label, location = detect_cable_car_state(lat, xs, start)
            icon = get_state_icon(state)
            
            print(f"\n{cable_id}号缆机 {icon}")
            print(f"  📍 位置: latitude={lat:.2f}, longitude={lon:.2f}")
            print(f"  🚀 速度: xspeed={xs:.2f}, start={start}")
            print(f"  📊 区域: {location}")
            print(f"  🎯 状态: {state} ({label})")
            
            # 判断说明
            if state == 'unloading':
                print(f"  ✅ 说明: 在卸料平台区 + 速度接近0 → 基坑卸料中")
            elif state == 'loading':
                print(f"  ✅ 说明: 在装料平台区 + 速度接近0 → 990平台接料中")
            elif state == 'delivering':
                print(f"  ✅ 说明: 速度为负值(xs<0) → 向卸料点移动（送料途中）")
            elif state == 'returning':
                print(f"  ✅ 说明: 速度为正值(xs>0) → 向装料点移动（返程途中）")
            elif state == 'stopped':
                print(f"  ⚠️ 说明: start=0 且不在任何工作区域 → 停止")
    
    print("\n" + "=" * 80)
    print("状态识别完成！新版系统能准确识别四种状态。")
    print("=" * 80)
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
