#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析 vehicle_system.datum_data 表 - 识别车辆在Y字形分叉路的行驶方向
"""

import pymysql
from datetime import datetime

DB_CONFIG = {
    'host': '192.168.1.88',
    'port': 3306,
    'user': 'root',
    'password': '!Tmhc20170717',
    'database': 'vehicle_system',
    'charset': 'utf8mb4'
}

def main():
    print("=" * 80)
    print("车辆运输方向分析 - Y字形分叉路")
    print("=" * 80)
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 1. 查看表结构
    print("\n【表结构】")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            COLUMN_COMMENT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = 'vehicle_system' 
        AND TABLE_NAME = 'datum_data'
        ORDER BY ORDINAL_POSITION
    """)
    columns = cursor.fetchall()
    
    print(f"{'字段名':<20} {'数据类型':<15} {'注释'}")
    print("-" * 60)
    for col in columns:
        print(f"{col[0]:<20} {col[1]:<15} {col[2] if col[2] else '-'}")
    
    # 2. 统计车辆数量和基本信息
    print("\n【车辆统计】")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT tid) as vehicle_count,
            COUNT(*) as total_records,
            MIN(time) as earliest,
            MAX(time) as latest
        FROM datum_data
    """)
    stats = cursor.fetchone()
    print(f"车辆总数: {stats[0]}")
    print(f"记录总数: {stats[1]}")
    print(f"时间范围: {stats[2]} ~ {stats[3]}")
    
    # 3. 按车辆查看最新状态
    print("\n【各车辆最新状态】")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            d.tid,
            d.user_name,
            d.result_x,
            d.result_y,
            d.lat,
            d.lon,
            d.speed,
            d.time,
            d.route
        FROM datum_data d
        INNER JOIN (
            SELECT tid, MAX(time) as max_time 
            FROM datum_data 
            GROUP BY tid
        ) latest ON d.tid = latest.tid AND d.time = latest.max_time
        ORDER BY d.tid
    """)
    vehicles = cursor.fetchall()
    
    print(f"{'车号':<8} {'车辆名':<12} {'result_x':<12} {'result_y':<12} {'lat':<10} {'lon':<10} {'速度':<8} {'时间':<20}")
    print("-" * 120)
    for v in vehicles:
        tid = v[0]
        name = v[1] if v[1] else '-'
        rx = f"{v[2]:.2f}" if v[2] else '-'
        ry = f"{v[3]:.2f}" if v[3] else '-'
        lat = f"{v[4]:.2f}" if v[4] else '-'
        lon = f"{v[5]:.2f}" if v[5] else '-'
        speed = f"{v[6]:.2f}" if v[6] else '0'
        time_str = str(v[7]) if v[7] else '-'
        print(f"{tid:<8} {name:<12} {rx:<12} {ry:<12} {lat:<10} {lon:<10} {speed:<8} {time_str:<20}")
    
    # 4. 分析坐标范围，确定右端和左端
    print("\n【坐标范围分析】")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            MIN(result_x) as min_x,
            MAX(result_x) as max_x,
            MIN(result_y) as min_y,
            MAX(result_y) as max_y,
            MIN(lat) as min_lat,
            MAX(lat) as max_lat,
            MIN(lon) as min_lon,
            MAX(lon) as max_lon
        FROM datum_data
    """)
    coord_stats = cursor.fetchone()
    
    print(f"result_x 范围: {coord_stats[0]:.2f} ~ {coord_stats[1]:.2f}")
    print(f"result_y 范围: {coord_stats[2]:.2f} ~ {coord_stats[3]:.2f}")
    print(f"lat 范围: {coord_stats[4]:.2f} ~ {coord_stats[5]:.2f}")
    print(f"lon 范围: {coord_stats[6]:.2f} ~ {coord_stats[7]:.2f}")
    
    # 根据图3分析，右端是起点（高X值），左端是终点（低X值）
    print("\n📍 基于Y字形分叉路分析：")
    print(f"   右端（起点/接料点）: result_x 约 {coord_stats[1]:.0f} 附近")
    print(f"   左端（终点/卸料点）: result_x 约 {coord_stats[0]:.0f} 附近")
    
    # 5. 分析每台车的行驶轨迹方向
    print("\n【车辆行驶方向分析】")
    print("=" * 80)
    
    for v in vehicles[:5]:  # 分析前5辆车
        tid = v[0]
        name = v[1]
        
        print(f"\n{'='*60}")
        print(f"车辆 {tid} ({name}) 轨迹分析:")
        print(f"{'='*60}")
        
        # 获取该车的轨迹数据（按时间排序）
        cursor.execute("""
            SELECT 
                result_x,
                result_y,
                lat,
                lon,
                speed,
                time
            FROM datum_data
            WHERE tid = %s
            ORDER BY time ASC
            LIMIT 20
        """, (tid,))
        
        trajectory = cursor.fetchall()
        
        if len(trajectory) >= 2:
            print(f"{'序号':<6} {'result_x':<12} {'result_y':<12} {'Δx':<10} {'方向':<15} {'速度':<8} {'时间'}")
            print("-" * 90)
            
            prev_x = None
            for i, point in enumerate(trajectory):
                curr_x = point[0]
                curr_y = point[1]
                lat = point[2]
                lon = point[3]
                speed = point[4]
                time_str = str(point[5]) if point[5] else '-'
                
                if prev_x is not None:
                    delta_x = curr_x - prev_x
                    
                    # 判断方向：X减小=向左（往卸料点），X增加=向右（返程）
                    if delta_x < -0.1:
                        direction = "←向左(往程)"
                    elif delta_x > 0.1:
                        direction = "→向右(返程)"
                    else:
                        direction = "-"
                    
                    print(f"{i:<6} {curr_x:<12.2f} {curr_y:<12.2f} {delta_x:+10.2f} {direction:<15} {speed if speed else 0:<8.2f} {time_str}")
                else:
                    print(f"{i:<6} {curr_x:<12.2f} {curr_y:<12.2f} {'-':<10} {'起点':<15} {speed if speed else 0:<8.2f} {time_str}")
                
                prev_x = curr_x
    
    # 6. 总结Y字形分叉路方向判断方法
    print("\n" + "=" * 80)
    print("【Y字形分叉路方向判断方法】")
    print("=" * 80)
    print("""
基于数据分析和图示，判断车辆从右端走向左端（往程）的特征：

┌─────────────────────────────────────────────────────────────────────────────┐
│ 1️⃣  坐标系分析                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ • result_x: 主方向坐标（沿道路方向）                                         │
│ • result_y: 横向坐标（垂直于道路方向，用于区分Y字形的不同分支）              │
│                                                                             │
│ 从图3可以看出：                                                              │
│ • 右端（起点）: result_x 值较大（高X值）                                     │
│ • 左端（终点）: result_x 值较小（低X值）                                     │
│ • Y字形分叉通过 result_y 的不同值来区分不同路线                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2️⃣  方向判断逻辑                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┬─────────────────┬─────────────────────────────────────┐│
│  │   Δ result_x    │     方向        │              说明                   ││
│  ├─────────────────┼─────────────────┼─────────────────────────────────────┤│
│  │   Δx < 0        │  ← 向左        │  往程：从右端(起点)向左端(终点)      ││
│  │   Δx > 0        │  → 向右        │  返程：从左端(终点)向右端(起点)      ││
│  │   Δx ≈ 0        │  - 静止/调整   │  在平台上等待或调整位置              ││
│  └─────────────────┴─────────────────┴─────────────────────────────────────┘│
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3️⃣  SQL判断方向                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ -- 判断车辆当前方向                                                         │
│ SELECT                                                                      │
│     tid,                                                                    │
│     user_name,                                                              │
│     result_x,                                                               │
│     result_y,                                                               │
│     speed,                                                                  │
│     LAG(result_x) OVER (PARTITION BY tid ORDER BY time) as prev_x,          │
│     CASE                                                                    │
│         WHEN result_x < LAG(result_x) OVER (PARTITION BY tid ORDER BY time) │
│         THEN '往程（向左/卸料）'                                             │
│         WHEN result_x > LAG(result_x) OVER (PARTITION BY tid ORDER BY time) │
│         THEN '返程（向右/接料）'                                             │
│         ELSE '静止/等待'                                                    │
│     END as direction                                                        │
│ FROM datum_data                                                             │
│ WHERE time >= DATE_SUB(NOW(), INTERVAL 5 MINUTE);  -- 最近5分钟数据        │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4️⃣  识别Y字形分叉路特征                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Y字形分叉路的特点：                                                          │
│ • 右端（起点）：多辆车聚集，result_x 值高                                    │
│ • 分叉点：result_y 值开始分散                                                │
│ • 左端（终点）：result_x 值低，车辆在此卸料                                  │
│                                                                             │
│ 识别车辆在哪条分支：                                                         │
│ • 通过 result_y 的值来区分不同分支                                           │
│ • 不同分支的 result_y 值范围不同                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
    """)
    
    # 7. 实际分析当前车辆的分布
    print("\n【当前车辆位置分布分析】")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            d.tid,
            d.user_name,
            d.result_x,
            d.result_y,
            CASE 
                WHEN d.result_x > 100 THEN '右端(起点)'
                WHEN d.result_x < 50 THEN '左端(终点)'
                ELSE '中途'
            END as location,
            d.speed,
            d.time
        FROM datum_data d
        INNER JOIN (
            SELECT tid, MAX(time) as max_time 
            FROM datum_data 
            GROUP BY tid
        ) latest ON d.tid = latest.tid AND d.time = latest.max_time
        ORDER BY d.result_x DESC
    """)
    
    current_positions = cursor.fetchall()
    
    print(f"{'车号':<8} {'车辆名':<12} {'result_x':<12} {'result_y':<12} {'位置':<15} {'速度':<8}")
    print("-" * 80)
    for pos in current_positions:
        tid = pos[0]
        name = pos[1] if pos[1] else '-'
        rx = f"{pos[2]:.2f}" if pos[2] else '-'
        ry = f"{pos[3]:.2f}" if pos[3] else '-'
        location = pos[4]
        speed = f"{pos[5]:.2f}" if pos[5] else '0'
        print(f"{tid:<8} {name:<12} {rx:<12} {ry:<12} {location:<15} {speed:<8}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("分析完成")
    print("=" * 80)

if __name__ == '__main__':
    main()
