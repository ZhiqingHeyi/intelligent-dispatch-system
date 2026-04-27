#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正后的缆机方向分析（送料时速度为正值）
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
    print("缆机方向分析 - 修正版（送料时速度为正值）")
    print("=" * 80)
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 获取当前状态
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
    
    print(f"{'缆机ID':<8} {'纬度(X)':<12} {'经度(Y)':<12} {'状态':<8} {'X速度':<10} {'Y速度':<10}")
    print("-" * 70)
    for row in rows:
        cable_id = row[0]
        lat = f"{row[1]:.2f}" if row[1] else '-'
        lon = f"{row[2]:.2f}" if row[2] else '-'
        status = '运行中' if row[4] == 1 else '停止'
        xs = f"{row[5]:.2f}" if row[5] else '0.00'
        ys = f"{row[6]:.2f}" if row[6] else '0.00'
        print(f"{cable_id:<8} {lat:<12} {lon:<12} {status:<8} {xs:<10} {ys:<10}")
    
    # 基于送料时速度为正值重新分析
    print("\n" + "=" * 80)
    print("【基于送料时速度为正值的方向判断】")
    print("=" * 80)
    
    analysis = []
    for row in rows:
        cable_id = row[0]
        lat = float(row[1]) if row[1] else 0
        lon = float(row[2]) if row[2] else 0
        start = row[4]
        xs = float(row[5]) if row[5] else 0
        ys = float(row[6]) if row[6] else 0
        
        total_speed = (xs**2 + ys**2)**0.5
        
        # 判断位置（优化：装料区下限从70调整到40，覆盖990平台休息区）
        if 40 <= lat <= 150:
            location = "装料平台区"
        elif lat >= 280:
            location = "卸料平台区"
        elif lat > 150 and lat < 280:
            location = "中途区域"
        else:
            location = "未知区域"
        
        # 判断方向（关键修正：送料=正值，返程=负值）
        if start == 0:
            direction = "🟡 停止/等待"
        else:
            if abs(xs) < 0.5 and abs(ys) < 0.5:
                direction = "🟡 运行中但速度低"
            elif xs > 0.5:
                direction = "🔴 往程（送料中，向卸料点）"
            elif xs < -0.5:
                direction = "🟢 返程（往回走，向装料点）"
            else:
                # X速度接近0，看Y速度
                if abs(ys) > 0.5:
                    direction = "🟡 横向移动中"
                else:
                    direction = "⚪ 其他"
        
        analysis.append({
            'id': cable_id,
            'lat': lat,
            'lon': lon,
            'location': location,
            'xs': xs,
            'ys': ys,
            'speed': total_speed,
            'direction': direction
        })
    
    print(f"\n{'缆机':<6} {'当前位置':<12} {'纬度':<10} {'X速度':<10} {'Y速度':<10} {'方向判断'}")
    print("-" * 90)
    for a in analysis:
        print(f"{a['id']:<6} {a['location']:<12} {a['lat']:<10.1f} {a['xs']:<10.2f} {a['ys']:<10.2f} {a['direction']}")
    
    # 返程特征总结
    print("\n" + "=" * 80)
    print("【返程（往回走）特征 - 修正版】")
    print("=" * 80)
    print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│ 关键结论：送料时 X速度 > 0（正值），返程时 X速度 < 0（负值）                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  📍 位置分布：                                                               │
│  • 装料平台区：latitude ≈ 79-132（缆机3、4当前在此）                         │
│  • 卸料平台区：latitude ≈ 300+（缆机2当前在此）                              │
│  • 中途区域：latitude 140-300（缆机1当前在此）                               │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  🔄 方向判断逻辑：                                                           │
│                                                                             │
│  ┌─────────────┬─────────────────┬─────────────────────────────────────────┐│
│  │   X速度     │     方向        │              说明                       ││
│  ├─────────────┼─────────────────┼─────────────────────────────────────────┤│
│  │   xs > 0    │  🔴 往程       │  送料中，从装料点向卸料点移动            ││
│  │   xs < 0    │  🟢 返程       │  往回走，从卸料点向装料点移动            ││
│  │   xs ≈ 0    │  🟡 横向/停止  │  在平台上或横向调整位置                  ││
│  └─────────────┴─────────────────┴─────────────────────────────────────────┘│
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  📊 当前各缆机状态解读：                                                      │
│                                                                             │
│  • 缆机1：X=-6.75（负值）→ 🟢 正在返程（从卸料点返回装料点）                 │
│  • 缆机2：X=0.00，Y=3.46 → 🟡 在卸料区横向调整位置                           │
│  • 缆机3：静止 → 🟡 在装料平台等待/装料中                                    │
│  • 缆机4：X=-0.66（负值）→ 🟢 正在返程（已从卸料点返回装料区）               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
    """)
    
    # SQL判断逻辑
    print("\n【返程判断SQL（修正版）】")
    print("-" * 80)
    print("""
-- 判断缆机方向（送料时xspeed为正）
SELECT 
    cable_car_id,
    latitude,
    xspeed,
    yspeed,
    CASE 
        WHEN start = 0 THEN '停止'
        WHEN xspeed > 0.5 THEN '往程（送料）'
        WHEN xspeed < -0.5 THEN '返程（往回走）'
        ELSE '平台区/调整中'
    END as direction,
    CASE
        WHEN latitude BETWEEN 40 AND 150 THEN '装料平台区'
        WHEN latitude >= 280 THEN '卸料平台区'
        ELSE '中途'
    END as location
FROM cable_car_status;
    """)
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("分析完成")
    print("=" * 80)

if __name__ == '__main__':
    main()
