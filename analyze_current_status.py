#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析当前缆机实时状态和返程特征（结合装料平台位置）
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

def main():
    print("=" * 80)
    print("当前缆机实时状态分析（结合装料平台位置）")
    print("=" * 80)
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 当前缆机状态（最新数据）
    print("\n【当前缆机实时状态】")
    print("-" * 80)
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
    
    print(f"{'缆机ID':<8} {'纬度(X)':<12} {'经度(Y)':<12} {'海拔(Z)':<10} {'状态':<8} {'X速度':<10} {'Y速度':<10}")
    print("-" * 80)
    for row in rows:
        cable_id = row[0]
        lat = f"{row[1]:.2f}" if row[1] else '-'
        lon = f"{row[2]:.2f}" if row[2] else '-'
        alt = f"{row[3]:.2f}" if row[3] else '-'
        status = '运行中' if row[4] == 1 else '停止'
        xs = f"{row[5]:.2f}" if row[5] else '0.00'
        ys = f"{row[6]:.2f}" if row[6] else '0.00'
        print(f"{cable_id:<8} {lat:<12} {lon:<12} {alt:<10} {status:<8} {xs:<10} {ys:<10}")
    
    # 分析当前位置特征
    print("\n【位置分析（基于装料平台位置）】")
    print("=" * 80)
    print("""
根据提供的信息：
• 缆机2、3 当前在装料平台
• 缆机2位置: latitude=132.40, longitude=27.60
• 缆机3位置: latitude=79.00, longitude=42.30

由此推断：
📍 装料平台位置区域: latitude ≈ 79-132（低纬度区域）
📍 卸料平台位置区域: latitude ≈ 339左右（高纬度区域）
    """)
    
    # 分析每台缆机的运动状态
    print("\n【各缆机运动方向分析】")
    print("-" * 80)
    
    analysis = []
    for row in rows:
        cable_id = row[0]
        lat = float(row[1]) if row[1] else 0
        lon = float(row[2]) if row[2] else 0
        start = row[4]
        xs = float(row[5]) if row[5] else 0
        ys = float(row[6]) if row[6] else 0
        
        # 计算合速度
        total_speed = (xs**2 + ys**2)**0.5
        
        # 判断是否在装料平台（latitude 79-132之间）
        if 70 <= lat <= 140:
            location = "装料平台区"
            if start == 0:
                state = "🟡 在装料平台，等待/停止"
            else:
                if total_speed > 0.1:
                    # 判断移动方向
                    if xs < 0:
                        state = "🔴 装料完成，开始往程（向卸料点）"
                    else:
                        state = "🟢 返程中（向装料点）"
                else:
                    state = "🟡 在装料平台，运行中但速度低"
        else:
            # 在高纬度区域（卸料区）
            if lat > 200:
                location = "卸料平台区"
                if start == 0:
                    state = "🔴 在卸料区，停止"
                else:
                    if total_speed > 0.1:
                        # 判断是往卸料点还是返程
                        if xs < 0 or ys > 0:
                            state = "🔴 往程中（向卸料点）"
                        else:
                            state = "🟢 返程中（向装料点）"
                    else:
                        state = "🟡 在卸料区附近，运行中"
            else:
                location = "中途"
                if start == 0:
                    state = "⚪ 中途停止"
                else:
                    # 根据速度和位置判断
                    if xs < -1:
                        state = "🔴 往程中（向卸料点）"
                    elif xs > 1:
                        state = "🟢 返程中（向装料点）"
                    else:
                        state = "🟡 运行中"
        
        analysis.append({
            'id': cable_id,
            'lat': lat,
            'location': location,
            'speed': total_speed,
            'state': state
        })
    
    print(f"{'缆机':<6} {'当前位置':<15} {'合速度':<10} {'状态判断'}")
    print("-" * 80)
    for a in analysis:
        print(f"{a['id']:<6} {a['location']:<15} {a['speed']:<10.2f} {a['state']}")
    
    # 返程特征总结
    print("\n" + "=" * 80)
    print("【返程（往回走）特征总结】")
    print("=" * 80)
    print("""
基于当前数据分析，缆机"往回走"（返程）的特征：

┌─────────────────────────────────────────────────────────────────────────────┐
│ 1️⃣  位置特征                                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ • 装料平台区域: latitude 约 79-132（缆机2、3当前在此）                        │
│ • 卸料平台区域: latitude 约 339左右（缆机1、4当前在此）                       │
│ • 返程判断: 从卸料平台（latitude大）向装料平台（latitude小）移动              │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2️⃣  速度方向特征（当前数据）                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ • 缆机1: xspeed=0.00, yspeed=3.50 → 主要向Y方向（可能往程或返程横向移动）      │
│ • 缆机2: xspeed=-6.76, yspeed=0.00 → 向X负方向移动（往程向卸料点）            │
│ • 缆机3: xspeed=0.00, yspeed=0.00 → 静止（在装料平台等待）                    │
│ • 缆机4: xspeed=0.60, yspeed=2.49 → 向X正、Y正方向（可能已卸货返程）          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3️⃣  返程判断逻辑                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ • 位置条件: latitude > 200（在卸料区或途中）                                  │
│ • 方向条件: 向latitude减小的方向移动（xspeed < 0 或在向装料平台靠近）         │
│ • 状态条件: start = 1（运行中）                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4️⃣  当前缆机返程状态判断                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ • 缆机1: 在卸料区，Y方向有速度 → 可能正在卸料或调整位置                       │
│ • 缆机2: 在装料区，X负方向快速移动 → 正在往程（装料完成向卸料点）             │
│ • 缆机3: 在装料区，静止 → 正在装料或等待                                      │
│ • 缆机4: 在卸料区，有X、Y方向速度 → 可能已完成卸货正在返程                    │
└─────────────────────────────────────────────────────────────────────────────┘
    """)
    
    # SQL查询示例
    print("\n【返程判断SQL查询示例】")
    print("-" * 80)
    print("""
-- 判断当前哪些缆机正在返程
SELECT 
    cable_car_id,
    latitude,
    longitude,
    xspeed,
    yspeed,
    CASE 
        WHEN latitude > 200 AND xspeed < -0.5 THEN '返程中'
        WHEN latitude > 200 AND xspeed >= -0.5 AND xspeed <= 0.5 THEN '卸料区'
        WHEN latitude BETWEEN 70 AND 140 THEN '装料平台区'
        WHEN latitude < 200 AND xspeed < -1 THEN '往程中'
        ELSE '其他状态'
    END as direction_status
FROM cable_car_status
WHERE start = 1;
    """)
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("分析完成")
    print("=" * 80)

if __name__ == '__main__':
    main()
