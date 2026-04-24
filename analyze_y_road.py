#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Y字形分叉路方向分析 - 深度分析
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
    print("Y字形分叉路深度分析 - 车辆方向识别")
    print("=" * 80)
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 1. 分析result_y的分布（Y字形分叉的关键）
    print("\n【Y字形分叉分析 - result_y分布】")
    print("=" * 80)
    
    cursor.execute("""
        SELECT 
            tid,
            user_name,
            result_x,
            result_y,
            CASE 
                WHEN result_y > 0 THEN '上分支(正Y)'
                WHEN result_y < -500 THEN '下分支(负Y)'
                ELSE '中间区域'
            END as branch,
            speed,
            time
        FROM datum_data
        ORDER BY result_y DESC
    """)
    
    vehicles = cursor.fetchall()
    
    print(f"{'车号':<6} {'车辆名':<10} {'result_x':<10} {'result_y':<12} {'所在分支':<15} {'速度':<8}")
    print("-" * 80)
    
    upper_branch = []  # 上分支（正Y）
    lower_branch = []  # 下分支（负Y）
    
    for v in vehicles:
        tid = v[0]
        name = v[1] if v[1] else '-'
        rx = f"{v[2]:.1f}" if v[2] else '-'
        ry = f"{v[3]:.1f}" if v[3] else '-'
        branch = v[4]
        speed = f"{v[5]:.1f}" if v[5] else '0'
        
        print(f"{tid:<6} {name:<10} {rx:<10} {ry:<12} {branch:<15} {speed:<8}")
        
        if v[3] > 0:
            upper_branch.append({'tid': tid, 'name': name, 'x': v[2], 'y': v[3]})
        elif v[3] < -500:
            lower_branch.append({'tid': tid, 'name': name, 'x': v[2], 'y': v[3]})
    
    # 2. 分析各分支特征
    print("\n【Y字形分叉路特征分析】")
    print("=" * 80)
    
    print(f"\n📍 上分支（result_y > 0）：{len(upper_branch)} 辆车")
    if upper_branch:
        avg_x = sum(v['x'] for v in upper_branch) / len(upper_branch)
        print(f"   平均 result_x: {avg_x:.1f}")
        print(f"   车辆: {', '.join([v['name'] for v in upper_branch])}")
    
    print(f"\n📍 下分支（result_y < -500）：{len(lower_branch)} 辆车")
    if lower_branch:
        avg_x = sum(v['x'] for v in lower_branch) / len(lower_branch)
        print(f"   平均 result_x: {avg_x:.1f}")
        print(f"   车辆: {', '.join([v['name'] for v in lower_branch])}")
    
    # 3. 方向判断核心逻辑
    print("\n" + "=" * 80)
    print("【识别从右端走向左端的核心逻辑】")
    print("=" * 80)
    print("""
基于坐标分析：

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Y字形分叉路坐标系                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│      左端(卸料点)                    右端(接料点/起点)                      │
│           │                               │                                 │
│           │    ← 往程方向 (X减小)          │                                 │
│           │                               │                                 │
│    ═══════╪═══════════════════════════════╪═══════  ← 主路                 │
│           │                               │                                 │
│           │    → 返程方向 (X增加)          │                                 │
│           │                               │                                 │
│     上分支│                               │下分支                          │
│    (正Y)  │                               │(负Y)                           │
│           │                               │                                 │
│           │                               │                                 │
│           │                               │                                 │
│     result_y > 0                    result_y < -500                          │
│                                                                             │
│  图示说明：                                                                  │
│  • 右端：result_x 值大（约200+），车辆在起点等待                             │
│  • 左端：result_x 值小（约0-10），车辆在卸料点                               │
│  • Y字形分叉通过 result_y 区分上/下两条路线                                  │
└─────────────────────────────────────────────────────────────────────────────┘
    """)
    
    # 4. SQL判断方法
    print("\n【SQL判断车辆方向和所在分支】")
    print("-" * 80)
    print("""
-- 方法1：判断车辆当前所在分支和位置
SELECT 
    tid,
    user_name,
    result_x,
    result_y,
    speed,
    CASE 
        WHEN result_y > 0 THEN '上分支'
        WHEN result_y < -500 THEN '下分支'
        ELSE '主路/中间'
    END as branch,
    CASE 
        WHEN result_x > 150 THEN '📍 右端(起点)'
        WHEN result_x < 20 THEN '📍 左端(终点)'
        ELSE '🚗 途中'
    END as position,
    CASE
        WHEN speed > 0.5 AND result_x < 200 THEN '🟢 运行中'
        WHEN speed = 0 THEN '🔴 停止'
        ELSE '🟡 低速'
    END as status
FROM datum_data
ORDER BY result_x DESC;

-- 方法2：判断行驶方向（需要连续轨迹点）
-- 通过比较前后两个时间点的result_x变化
SELECT 
    tid,
    user_name,
    result_x,
    result_y,
    time,
    LAG(result_x) OVER (PARTITION BY tid ORDER BY time) as prev_x,
    CASE 
        WHEN result_x < LAG(result_x) OVER (PARTITION BY tid ORDER BY time) 
        THEN '← 往程(向右端走向左端)'
        WHEN result_x > LAG(result_x) OVER (PARTITION BY tid ORDER BY time) 
        THEN '→ 返程(向左端走向右端)'
        ELSE '- 静止'
    END as direction
FROM datum_data
WHERE time >= '2026-04-24'  -- 当天数据
ORDER BY tid, time;
    """)
    
    # 5. 当前车辆状态汇总
    print("\n【当前车辆状态汇总】")
    print("=" * 80)
    
    cursor.execute("""
        SELECT 
            tid,
            user_name,
            result_x,
            result_y,
            speed,
            CASE 
                WHEN result_y > 0 THEN '上分支'
                WHEN result_y <