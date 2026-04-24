#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于Y坐标变化分析车辆行驶方向
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
    print("基于Y坐标变化的行驶方向分析")
    print("=" * 80)
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 分析Y坐标范围
    print("\n【Y坐标范围分析】")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            MIN(result_y) as min_y,
            MAX(result_y) as max_y,
            MIN(result_x) as min_x,
            MAX(result_x) as max_x
        FROM datum_data
    """)
    y_range = cursor.fetchone()
    
    print(f"Y坐标范围: {y_range[0]:.2f} ~ {y_range[1]:.2f}")
    print(f"X坐标范围: {y_range[2]:.2f} ~ {y_range[3]:.2f}")
    
    print("\n📍 基于图示分析：")
    print("   右端（起点）: result_y ≈ -338 附近（Y值较大）")
    print("   左端（终点）: result_y ≈ -1000 附近（Y值较小）")
    print("   往程方向: Y值逐渐减小（从右向左）")
    print("   返程方向: Y值逐渐增大（从左向右）")
    
    # 按Y坐标分析车辆位置
    print("\n【车辆Y坐标位置分析】")
    print("=" * 80)
    cursor.execute("""
        SELECT 
            tid,
            user_name,
            result_x,
            result_y,
            speed,
            CASE 
                WHEN result_y > -400 THEN '右端区域(起点)'
                WHEN result_y BETWEEN -600 AND -400 THEN '右中段'
                WHEN result_y BETWEEN -800 AND -600 THEN '左中段'
                WHEN result_y < -800 THEN '左端区域(终点)'
                ELSE '未知'
            END as y_zone,
            CASE
                WHEN result_y > -400 THEN 1
                WHEN result_y BETWEEN -600 AND -400 THEN 2
                WHEN result_y BETWEEN -800 AND -600 THEN 3
                WHEN result_y < -800 THEN 4
                ELSE 0
            END as zone_order
        FROM datum_data
        ORDER BY result_y DESC
    """)
    
    vehicles = cursor.fetchall()
    
    print(f"{'车号':<6} {'车辆名':<10} {'X坐标':<10} {'Y坐标':<12} {'Y区域':<20} {'速度':<8}")
    print("-" * 80)
    
    for v in vehicles:
        tid = v[0]
        name = v[1] if v[1] else '-'
        rx = f"{v[2]:.1f}" if v[2] else '-'
        ry = f"{v[3]:.1f}" if v[3] else '-'
        zone = v[5]
        speed = f"{v[4]:.1f}" if v[4] else '0'
        print(f"{tid:<6} {name:<10} {rx:<10} {ry:<12} {zone:<20} {speed:<8}")
    
    # 统计各区域车辆数量
    print("\n【各区域车辆分布】")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            CASE 
                WHEN result_y > -400 THEN '右端区域(起点)'
                WHEN result_y BETWEEN -600 AND -400 THEN '右中段'
                WHEN result_y BETWEEN -800 AND -600 THEN '左中段'
                WHEN result_y < -800 THEN '左端区域(终点)'
                ELSE '其他'
            END as y_zone,
            COUNT(*) as count,
            AVG(speed) as avg_speed
        FROM datum_data
        GROUP BY y_zone
        ORDER BY MIN(result_y) DESC
    """)
    
    zones = cursor.fetchall()
    print(f"{'区域':<20} {'车辆数':<10} {'平均速度':<10}")
    print("-" * 50)
    for z in zones:
        zone_name = z[0]
        count = z[1]
        avg_speed = f"{z[2]:.2f}" if z[2] else '0.00'
        print(f"{zone_name:<20} {count:<10} {avg_speed:<10}")
    
    # Y方向判断逻辑
    print("\n" + "=" * 80)
    print("【基于Y坐标的行驶方向判断逻辑】")
    print("=" * 80)
    print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│                         基于Y坐标的方向判断                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  图示：                                                                      │
│                                                                             │
│   右端(起点)         右中段        左中段         左端(终点)                │
│      │                │              │               │                     │
│  Y=-338 ────────── Y=-500 ──── Y=-700 ─────── Y=-1000                      │
│      │                │              │               │                     │
│      │  ← 往程 (Y减小)│              │               │                     │
│      │                │              │               │                     │
│      │  → 返程 (Y增加)│              │               │                     │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  判断逻辑：                                                                  │
│                                                                             │
│  1. 连续轨迹点Y值变化判断：                                                   │
│     • ΔY < -10（Y明显减小）→ 往程（从右端向左端）                            │
│     • ΔY > 10（Y明显增加）  → 返程（从左端向右端）                           │
│     • |ΔY| <= 10           → 静止或信号跳跃                                  │
│                                                                             │
│  2. 位置区域判断：                                                           │
│     • Y > -400              → 右端区域（起点）                               │
│     • -600 < Y <= -400      → 右中段                                         │
│     • -800 < Y <= -600      → 左中段                                         │
│     • Y <= -800             → 左端区域（终点/分叉点）                        │
│                                                                             │
│  3. 信号跳跃处理：                                                           │
│     • 由于定位基站较少，信号可能有跳跃                                       │
│     • 需要设置阈值（如|ΔY|>10才认为有方向变化）                              │
│     • 结合连续多个点判断趋势                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
    """)
    
    # SQL判断语句
    print("\n【SQL判断方向（基于Y坐标）】")
    print("-" * 80)
    print("""
-- 方法1：判断当前车辆所在区域
SELECT 
    tid,
    user_name,
    result_y,
    speed,
    CASE 
        WHEN result_y > -400 THEN '右端起点区'
        WHEN result_y BETWEEN -600 AND -400 THEN '右中段'
        WHEN result_y BETWEEN -800 AND -600 THEN '左中段'
        WHEN result_y <= -800 THEN '左端终点区'
    END as y_zone,
    CASE
        WHEN speed > 0 THEN '运行中'
        ELSE '停止'
    END as status
FROM datum_data;

-- 方法2：判断行驶方向（基于Y变化）
SELECT 
    tid,
    result_y,
    time,
    LAG(result_y) OVER (PARTITION BY tid ORDER BY time) as prev_y,
    result_y - LAG(result_y) OVER (PARTITION BY tid ORDER BY time) as delta_y,
    CASE 
        WHEN result_y - LAG(result_y) OVER (...) < -10 THEN '往程(右→左)'
        WHEN result_y - LAG(result_y) OVER (...) > 10 THEN '返程(左→右)'
        ELSE '静止/跳跃'
    END as direction
FROM datum_data
WHERE time >= CURDATE();

-- 方法3：判断是否在往程（从右端走向左端）
-- 条件：Y值在减小，且当前Y在-338到-1000之间
SELECT 
    tid,
    user_name,
    result_y,
    speed,
    CASE 
        WHEN result_y BETWEEN -1000 AND -338 AND speed > 0
        THEN '在道路区间内'
        ELSE '在区间外'
    END as in_range
FROM datum_data;
    """)
    
    print("\n" + "=" * 80)
    print("【总结】")
    print("=" * 80)
    print("""
基于Y坐标判断车辆从右端走向左端的方法：

✅ 核心逻辑：
   • Y值从 -338 → -1000（逐渐减小）→ 往程（从右向左）
   • Y值从 -1000 → -338（逐渐增大）→ 返程（从左向右）

✅ 阈值设置：
   • |ΔY| > 10 认为有方向变化（过滤信号跳跃）
   • 连续2-3个点同向变化确认方向

✅ 关键SQL：
   SELECT *,
       CASE 
           WHEN result_y < LAG(result_y) OVER (PARTITION BY tid ORDER BY time) 
                AND ABS(result_y - LAG(result_y) OVER (...)) > 10
           THEN '往程(右→左)'
           WHEN result_y > LAG(result_y) OVER (...) 
                AND ABS(result_y - LAG(result_y) OVER (...)) > 10
           THEN '返程(左→右)'
           ELSE '静止'
       END as direction
   FROM datum_data;
    """)
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
