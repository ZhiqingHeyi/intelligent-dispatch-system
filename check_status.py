#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查缆机实时状态 - 特别验证1/2/3号返程状态
"""

import pymysql
from datetime import datetime

DB_CONFIG = {
    'host': '192.168.1.88',
    'port': 3306,
    'user': 'root',
    'password': '!Tmhc20170717',
    'database': 'cable_car',
    'charset': 'utf8mb4'
}

# 系统判断逻辑（来自data_sync.py）
CABLE_CAR_RETURN_THRESHOLD = -0.5

def detect_cable_car_direction(xspeed, start):
    if start == 0:
        return 'stopped', '停止'
    if xspeed > CABLE_CAR_RETURN_THRESHOLD:  # > -0.5
        return 'going', '送料中'
    if xspeed < -CABLE_CAR_RETURN_THRESHOLD: # < -0.5
        return 'returning', '返程中🟢'
    return 'idle', '待命'

def main():
    print("=" * 80)
    print("缆机实时状态检查 - 重点查看1/2/3号返程状态")
    print("=" * 80)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"返程阈值: xspeed < {CABLE_CAR_RETURN_THRESHOLD}")
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
    
    print("\n【缆机实时状态详细分析】")
    print("-" * 100)
    print(f"{'缆机ID':<8} {'纬度(X)':<12} {'经度(Y)':<12} {'启动':<6} {'X速度':<10} {'Y速度':<10} {'系统判断':<12} {'状态'}")
    print("-" * 100)
    
    returning_count = 0
    
    for row in rows:
        cable_id = row[0]
        lat = row[1] if row[1] else 0
        lon = row[2] if row[2] else 0
        start = row[4] if row[4] else 0
        xs = row[5] if row[5] else 0
        ys = row[6] if row[6] else 0
        
        direction_code, direction_label = detect_cable_car_direction(xs, start)
        
        # 位置区域判断
        if 70 <= lat <= 140:
            location = "装料平台区"
        elif lat >= 300:
            location = "卸料平台区"
        elif lat > 140 and lat < 300:
            location = "中途区域"
        else:
            location = "其他"
        
        if direction_code == 'returning':
            returning_count += 1
            marker = "✅ 返程"
        else:
            marker = ""
        
        start_str = '运行' if start == 1 else '停止'
        
        print(f"{cable_id:<8} {lat:<12.2f} {lon:<12.2f} {start_str:<6} {xs:<10.2f} {ys:<10.2f} {direction_label:<12} {marker}")
    
    print("-" * 100)
    
    # 特别标注1/2/3号
    print("\n【1/2/3号缆机状态重点关注】")
    print("-" * 80)
    for row in rows:
        cable_id = row[0]
        if cable_id in [1, 2, 3]:
            lat = row[1] if row[1] else 0
            start = row[4] if row[4] else 0
            xs = row[5] if row[5] else 0
            
            direction_code, direction_label = detect_cable_car_direction(xs, start)
            
            print(f"\n{cable_id}号缆机:")
            print(f"  位置: latitude={lat:.2f}")
            print(f"  X速度: {xs:.2f}")
            print(f"  系统判断: {direction_label}")
            
            if direction_code == 'returning':
                print(f"  ⚠️ 注意: 系统已识别为返程中")
            elif direction_code == 'going':
                print(f"  ℹ️ 注意: 系统识别为送料中（xspeed={xs:.2f} > -0.5）")
            elif direction_code == 'idle':
                print(f"  ℹ️ 注意: 系统识别为待命（xspeed={xs:.2f}在-0.5~0.5之间）")
            elif direction_code == 'stopped':
                print(f"  ℹ️ 注意: 系统识别为停止（start={start}）")
    
    print("\n" + "=" * 80)
    print(f"当前返程缆机数量: {returning_count} 台")
    print("=" * 80)
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
