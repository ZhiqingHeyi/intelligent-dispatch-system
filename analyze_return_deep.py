#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度分析缆机返程特征 - 查找实际返程记录
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
    print("缆机返程特征深度分析")
    print("=" * 80)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 获取全部轨迹数据，分析方向变化
    cursor.execute("""
        SELECT 
            id,
            latitude,
            longitude,
            timestamp,
            status,
            speed
        FROM cable_car_positions
        WHERE cableCarId = 5
        ORDER BY timestamp ASC
    """)
    rows = cursor.fetchall()
    
    print(f"\n总记录数: {len(rows)}")
    
    # 分析每个轨迹点的方向变化
    print("\n【完整轨迹方向分析】")
    print("-" * 80)
    
    direction_changes = []
    return_segments = []  # 返程段
    go_segments = []      # 往程段
    
    for i in range(1, len(rows)):
        prev = rows[i-1]
        curr = rows[i]
        
        prev_lat = prev[1]
        curr_lat = curr[1]
        
        if prev_lat is not None and curr_lat is not None:
            delta = curr_lat - prev_lat
            
            # 判断方向：纬度增加=返程(向北)，纬度减少=往程(向南)
            if delta > 0.5:  # 纬度明显增加
                direction = "返程↑"
                return_segments.append({
                    'time': curr[3],
                    'lat': curr_lat,
                    'delta': delta,
                    'status': curr[4]
                })
            elif delta < -0.5:  # 纬度明显减少
                direction = "往程↓"
                go_segments.append({
                    'time': curr[3],
                    'lat': curr_lat,
                    'delta': delta,
                    'status': curr[4]
                })
            else:
                direction = "-"
            
            if abs(delta) > 0.5:
                direction_changes.append({
                    'time': curr[3],
                    'from_lat': prev_lat,
                    'to_lat': curr_lat,
                    'delta': delta,
                    'direction': direction,
                    'status': curr[4]
                })
    
    print(f"方向变化点数: {len(direction_changes)}")
    print(f"往程段点数: {len(go_segments)}")
    print(f"返程段点数: {len(return_segments)}")
    
    # 显示前20个方向变化点
    print("\n【方向变化详情（前30个）】")
    print(f"{'时间':<20} {'从纬度':<12} {'到纬度':<12} {'变化':<10} {'方向':<10} {'状态'}")
    print("-" * 80)
    for dc in direction_changes[:30]:
        ts = dc['time'].strftime('%H:%M:%S') if dc['time'] else '-'
        print(f"{ts:<20} {dc['from_lat']:<12.2f} {dc['to_lat']:<12.2f} {dc['delta']:+8.2f}   {dc['direction']:<10} {dc['status']}")
    
    # 显示所有返程记录
    if return_segments:
        print("\n【返程记录汇总】")
        print("-" * 80)
        print(f"发现 {len(return_segments)} 个返程轨迹点")
        print(f"{'时间':<20} {'纬度':<12} {'变化':<10} {'状态'}")
        print("-" * 60)
        for rs in return_segments:
            ts = rs['time'].strftime('%H:%M:%S') if rs['time'] else '-'
            print(f"{ts:<20} {rs['lat']:<12.2f} {rs['delta']:+8.2f}   {rs['status']}")
    else:
        print("\n【返程记录】")
        print("-" * 80)
        print("⚠️ 当前数据中未发现明显的返程记录（纬度增加）")
        print("   可能原因：")
        print("   1. 数据只记录了一小段往程过程")
        print("   2. 返程时的状态标记可能不同")
        print("   3. 数据采样的时间段刚好只有往程")
    
    # 分析最小最大纬度点
    print("\n【极值点分析】")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            (SELECT timestamp FROM cable_car_positions WHERE cableCarId = 5 ORDER BY latitude DESC LIMIT 1) as max_lat_time,
            (SELECT latitude FROM cable_car_positions WHERE cableCarId = 5 ORDER BY latitude DESC LIMIT 1) as max_lat,
            (SELECT timestamp FROM cable_car_positions WHERE cableCarId = 5 ORDER BY latitude ASC LIMIT 1) as min_lat_time,
            (SELECT latitude FROM cable_car_positions WHERE cableCarId = 5 ORDER BY latitude ASC LIMIT 1) as min_lat
    """)
    extreme = cursor.fetchone()
    
    if extreme:
        print(f"最大纬度点: {extreme[1]:.2f} @ {extreme[0]}")
        print(f"最小纬度点: {extreme[3]:.2f} @ {extreme[2]}")
        print(f"\n📍 装料点（高纬度）: 约 {extreme[1]:.0f}")
        print(f"📍 卸料点（低纬度）: 约 {extreme[3]:.0f}")
    
    # 结合系统截图分析返程特征
    print("\n" + "=" * 80)
    print("【结合监控系统的返程特征总结】")
    print("=" * 80)
    print("""
根据数据库分析和系统界面，缆机"往回走"（返程）的特征：

┌─────────────────────────────────────────────────────────────────────────────┐
│ 1️⃣  位置坐标特征                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ • 装料点位置：纬度(X) ≈ 780 左右（高纬度端）                                  │
│ • 卸料点位置：纬度(X) ≈ 70 左右（低纬度端）                                   │
│ • 返程判断：当纬度值持续增加时（从低到高），即为返程                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2️⃣  方向变化特征                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ • 往程（装料→卸料）：纬度递减（Δ纬度 < 0），向南运动                          │
│ • 返程（卸料→装料）：纬度递增（Δ纬度 > 0），向北运动                          │
│ • 系统界面显示有"距离卸料平台距离"和"距离倒仓位置距离"指标                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3️⃣  状态字段特征                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ • 当前数据中所有记录 status = 'start'                                        │
│ • 可能的业务状态：                                                           │
│   - 'start': 启动/运行中（可能包括往返全程）                                  │
│   - 'loading': 正在装料                                                      │
│   - 'unloading': 正在卸料                                                    │
│   - 'empty': 空载返程                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4️⃣  速度特征                                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ • 满载往程：速度约 3-5 m/s                                                   │
│ • 空载返程：速度可能不同（需更多数据分析）                                    │
│ • 当前数据显示速度在 2.5-6 m/s 范围内波动                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5️⃣  数据库判断返程的SQL逻辑                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ -- 方法1：根据连续轨迹点纬度变化判断                                          │
│ SELECT 
│   cableCarId,
│   timestamp,
│   latitude,
│   LAG(latitude) OVER (PARTITION BY cableCarId ORDER BY timestamp) as prev_lat,
│   CASE 
│     WHEN latitude > LAG(latitude) OVER (PARTITION BY cableCarId ORDER BY timestamp) 
│     THEN '返程'
│     ELSE '往程'
│   END as direction
│ FROM cable_car_positions;
│
│ -- 方法2：根据已知装料/卸料点位置判断                                         │
│ -- 当缆车从低纬度(卸料点)向高纬度(装料点)移动时，即为返程                      │
└─────────────────────────────────────────────────────────────────────────────┘
    """)
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
