#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析缆机"往回走"（返程）的特征
"""

import pymysql
from datetime import datetime

# 数据库连接配置
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
    print("缆机返程特征分析")
    print("=" * 80)
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 1. 查看缆机5号的历史轨迹（按时间排序）
        print("\n【缆机5号轨迹数据抽样分析】")
        print("-" * 80)
        cursor.execute("""
            SELECT 
                id,
                latitude,
                longitude,
                altitude,
                status,
                speed,
                timestamp
            FROM cable_car_positions
            WHERE cableCarId = 5
            ORDER BY timestamp ASC
            LIMIT 100
        """)
        rows = cursor.fetchall()
        
        if rows:
            print(f"{'序号':<6} {'纬度(X)':<15} {'经度(Y)':<15} {'海拔(Z)':<10} {'状态':<10} {'速度':<10} {'时间戳'}")
            print("-" * 100)
            for i, row in enumerate(rows[:20], 1):  # 显示前20条
                lat = f"{row[1]:.2f}" if row[1] else '-'
                lon = f"{row[2]:.2f}" if row[2] else '-'
                alt = f"{row[3]:.2f}" if row[3] else '-'
                status = row[4] if row[4] else '-'
                speed = f"{row[5]:.2f}" if row[5] else '-'
                ts = row[6].strftime('%H:%M:%S') if row[6] else '-'
                print(f"{i:<6} {lat:<15} {lon:<15} {alt:<10} {status:<10} {speed:<10} {ts}")
        
        # 2. 分析轨迹变化趋势
        print("\n【轨迹变化趋势分析】")
        print("-" * 80)
        cursor.execute("""
            SELECT 
                MIN(latitude) as min_lat,
                MAX(latitude) as max_lat,
                AVG(latitude) as avg_lat,
                MIN(longitude) as min_lon,
                MAX(longitude) as max_lon,
                AVG(longitude) as avg_lon,
                MIN(altitude) as min_alt,
                MAX(altitude) as max_alt
            FROM cable_car_positions
            WHERE cableCarId = 5
        """)
        stats = cursor.fetchone()
        
        if stats:
            print(f"纬度(X)范围: {stats[0]:.2f} ~ {stats[1]:.2f}, 平均值: {stats[2]:.2f}")
            print(f"经度(Y)范围: {stats[3]:.2f} ~ {stats[4]:.2f}, 平均值: {stats[5]:.2f}")
            print(f"海拔(Z)范围: {stats[6]:.2f} ~ {stats[7]:.2f}")
        
        # 3. 按状态分析
        print("\n【按状态统计】")
        print("-" * 80)
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count,
                MIN(timestamp) as earliest,
                MAX(timestamp) as latest,
                AVG(latitude) as avg_lat,
                AVG(longitude) as avg_lon
            FROM cable_car_positions
            WHERE cableCarId = 5
            GROUP BY status
            ORDER BY count DESC
        """)
        status_stats = cursor.fetchall()
        
        print(f"{'状态':<15} {'记录数':<10} {'最早时间':<20} {'最晚时间':<20} {'平均纬度':<12} {'平均经度':<12}")
        print("-" * 100)
        for stat in status_stats:
            status = stat[0] if stat[0] else 'NULL'
            count = stat[1]
            earliest = stat[2].strftime('%Y-%m-%d %H:%M') if stat[2] else '-'
            latest = stat[3].strftime('%Y-%m-%d %H:%M') if stat[3] else '-'
            avg_lat = f"{stat[4]:.2f}" if stat[4] else '-'
            avg_lon = f"{stat[5]:.2f}" if stat[5] else '-'
            print(f"{status:<15} {count:<10,} {earliest:<20} {latest:<20} {avg_lat:<12} {avg_lon:<12}")
        
        # 4. 分析连续轨迹点变化
        print("\n【连续轨迹点变化分析（判断往返特征）】")
        print("-" * 80)
        cursor.execute("""
            SELECT 
                id,
                latitude,
                longitude,
                timestamp,
                status
            FROM cable_car_positions
            WHERE cableCarId = 5
            ORDER BY timestamp ASC
            LIMIT 200
        """)
        trajectory = cursor.fetchall()
        
        if len(trajectory) >= 2:
            # 计算方向变化
            print("\n轨迹方向变化分析（前20个相邻点）:")
            print(f"{'序号':<6} {'纬度':<12} {'经度':<12} {'Δ纬度':<10} {'Δ经度':<10} {'方向':<15} {'状态'}")
            print("-" * 90)
            
            for i in range(1, min(20, len(trajectory))):
                prev = trajectory[i-1]
                curr = trajectory[i]
                
                delta_lat = curr[1] - prev[1]
                delta_lon = curr[2] - prev[2]
                
                # 判断方向
                if abs(delta_lat) > abs(delta_lon):
                    direction = "向南" if delta_lat < 0 else "向北"
                else:
                    direction = "向西" if delta_lon < 0 else "向东"
                
                lat_str = f"{curr[1]:.2f}"
                lon_str = f"{curr[2]:.2f}"
                dlat_str = f"{delta_lat:+.2f}"
                dlon_str = f"{delta_lon:+.2f}"
                status = curr[4] if curr[4] else '-'
                
                print(f"{i:<6} {lat_str:<12} {lon_str:<12} {dlat_str:<10} {dlon_str:<10} {direction:<15} {status}")
        
        # 5. 分析返程特征
        print("\n【返程特征判断方法】")
        print("=" * 80)
        print("""
根据轨迹数据分析，判断缆机"往回走"（返程）的特征：

1. 【位置特征】
   - 装料点位置: 纬度较高 (约780附近)
   - 卸料点位置: 纬度较低 (约79-230附近)
   
   返程判断: 当纬度值从小(卸料点)向大(装料点)方向移动时，即为返程

2. 【状态特征】
   - 从表中可以看到 'status' 字段有值如 'start'
   - 可能的业务逻辑：
     * 'start' - 空载前往装料点
     * 'load'/'running' - 满载前往卸料点
     * 'return' - 卸料后返程

3. 【速度特征】
   - 空载返程时速度可能不同于满载运行时
   - 可对比不同status下的平均速度

4. 【高度特征】
   - 海拔高度可能在不同阶段有变化
   - 装料点和卸料点可能有高度差

5. 【轨迹方向变化】
   - 往程：纬度从大→小（向卸料点）
   - 返程：纬度从小→大（向装料点）
        """)
        
        # 6. 实际数据分析
        print("\n【实际数据中的往返特征验证】")
        print("-" * 80)
        
        # 获取一段时间内的轨迹，分析方向变化
        cursor.execute("""
            SELECT 
                timestamp,
                latitude,
                longitude,
                status,
                LAG(latitude) OVER (ORDER BY timestamp) as prev_lat
            FROM cable_car_positions
            WHERE cableCarId = 5
            ORDER BY timestamp ASC
            LIMIT 50
        """)
        direction_data = cursor.fetchall()
        
        print(f"{'时间':<20} {'纬度':<12} {'变化':<10} {'方向':<10} {'状态'}")
        print("-" * 70)
        
        for row in direction_data[1:]:  # 跳过第一条（无前一个点）
            ts = row[0].strftime('%H:%M:%S') if row[0] else '-'
            lat = row[1]
            prev_lat = row[4]
            
            if lat and prev_lat:
                change = lat - prev_lat
                if abs(change) > 0.1:
                    direction = "返程↑" if change > 0 else "往程↓"
                    status = row[3] if row[3] else '-'
                    print(f"{ts:<20} {lat:<12.2f} {change:+.2f}      {direction:<10} {status}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print("分析完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
