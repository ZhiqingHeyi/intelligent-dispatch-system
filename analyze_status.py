#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析 cable_car_status 表 - 缆机实时状态信息
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

def format_bytes(size):
    """格式化字节大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def main():
    print("=" * 80)
    print("cable_car_status 表分析报告 - 缆机实时状态信息")
    print("=" * 80)
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库: cable_car@192.168.1.88:3306")
    print("=" * 80)
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 1. 表结构
        print("\n【表结构】")
        print("-" * 80)
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                NUMERIC_PRECISION,
                NUMERIC_SCALE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                COLUMN_COMMENT,
                EXTRA
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'cable_car' 
            AND TABLE_NAME = 'cable_car_status'
            ORDER BY ORDINAL_POSITION
        """)
        structure = cursor.fetchall()
        
        print(f"{'字段名':<20} {'数据类型':<15} {'长度':<10} {'允许空':<8} {'默认值':<20} {'注释':<20}")
        print("-" * 80)
        
        for col in structure:
            col_name = col[0]
            data_type = col[1]
            max_length = col[2] if col[2] else (col[3] if col[3] else '-')
            is_nullable = '是' if col[5] == 'YES' else '否'
            default = str(col[6]) if col[6] is not None else 'NULL'
            comment = col[7] if col[7] else '-'
            
            print(f"{col_name:<20} {data_type:<15} {str(max_length):<10} {is_nullable:<8} {default:<20} {comment:<20}")
        
        # 2. 表统计信息
        print("\n【表统计信息】")
        print("-" * 80)
        cursor.execute("""
            SELECT 
                TABLE_ROWS,
                DATA_LENGTH,
                INDEX_LENGTH,
                DATA_LENGTH + INDEX_LENGTH AS TOTAL_LENGTH,
                CREATE_TIME,
                UPDATE_TIME
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'cable_car' 
            AND TABLE_NAME = 'cable_car_status'
        """)
        stats = cursor.fetchone()
        if stats:
            print(f"记录总数:     {stats[0]:,} 条")
            print(f"数据大小:     {format_bytes(stats[1])}")
            print(f"索引大小:     {format_bytes(stats[2])}")
            print(f"总大小:       {format_bytes(stats[3])}")
            print(f"创建时间:     {stats[4]}")
            print(f"更新时间:     {stats[5]}")
        
        # 3. 索引信息
        print("\n【索引信息】")
        print("-" * 80)
        cursor.execute("""
            SELECT 
                INDEX_NAME,
                COLUMN_NAME,
                NON_UNIQUE,
                SEQ_IN_INDEX
            FROM INFORMATION_SCHEMA.STATISTICS 
            WHERE TABLE_SCHEMA = 'cable_car' 
            AND TABLE_NAME = 'cable_car_status'
            ORDER BY INDEX_NAME, SEQ_IN_INDEX
        """)
        indexes = cursor.fetchall()
        
        if indexes:
            current_index = None
            index_columns = []
            for idx in indexes:
                if idx[0] != current_index:
                    if current_index:
                        unique = "唯一" if not index_columns[0][2] else "普通"
                        cols = ", ".join([c[1] for c in index_columns])
                        print(f"  {current_index:<30} {unique:<8} {cols}")
                    current_index = idx[0]
                    index_columns = []
                index_columns.append(idx)
            
            if current_index:
                unique = "唯一" if not index_columns[0][2] else "普通"
                cols = ", ".join([c[1] for c in index_columns])
                print(f"  {current_index:<30} {unique:<8} {cols}")
        else:
            print("  暂无索引信息")
        
        # 4. 当前所有缆机状态
        print("\n【当前所有缆机实时状态】")
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
        
        if rows:
            print(f"{'缆机ID':<10} {'纬度(X)':<12} {'经度(Y)':<12} {'海拔(Z)':<12} {'启动':<8} {'X速度':<10} {'Y速度':<10} {'更新时间':<20}")
            print("-" * 100)
            for row in rows:
                cable_id = row[0]
                lat = f"{row[1]:.2f}" if row[1] is not None else '-'
                lon = f"{row[2]:.2f}" if row[2] is not None else '-'
                alt = f"{row[3]:.2f}" if row[3] is not None else '-'
                start = '运行中' if row[4] == 1 else '停止' if row[4] == 0 else str(row[4])
                xspeed = f"{row[5]:.2f}" if row[5] is not None else '-'
                yspeed = f"{row[6]:.2f}" if row[6] is not None else '-'
                updated = row[7].strftime('%Y-%m-%d %H:%M:%S') if row[7] else '-'
                
                print(f"{cable_id:<10} {lat:<12} {lon:<12} {alt:<12} {start:<8} {xspeed:<10} {yspeed:<10} {updated:<20}")
        else:
            print("表中暂无数据")
        
        # 5. 统计信息
        print("\n【状态统计】")
        print("-" * 80)
        cursor.execute("""
            SELECT 
                start,
                COUNT(*) as count
            FROM cable_car_status
            GROUP BY start
        """)
        status_stats = cursor.fetchall()
        
        print("按启动状态统计:")
        for stat in status_stats:
            status_desc = '运行中' if stat[0] == 1 else '停止' if stat[0] == 0 else f'未知({stat[0]})'
            print(f"  {status_desc}: {stat[1]} 台缆机")
        
        # 6. 速度统计
        print("\n【速度统计】")
        print("-" * 80)
        cursor.execute("""
            SELECT 
                cable_car_id,
                ROUND(SQRT(POW(xspeed, 2) + POW(yspeed, 2)), 2) as total_speed,
                xspeed,
                yspeed
            FROM cable_car_status
            ORDER BY total_speed DESC
        """)
        speed_stats = cursor.fetchall()
        
        if speed_stats:
            print(f"{'缆机ID':<10} {'合速度':<12} {'X速度':<12} {'Y速度':<12} {'状态'}")
            print("-" * 60)
            for row in speed_stats:
                cable_id = row[0]
                total = row[1] if row[1] is not None else 0
                xs = row[2] if row[2] is not None else 0
                ys = row[3] if row[3] is not None else 0
                
                if total == 0:
                    status = "静止"
                elif total < 1:
                    status = "低速"
                elif total < 5:
                    status = "中速"
                else:
                    status = "高速"
                
                print(f"{cable_id:<10} {total:<12.2f} {xs:<12.2f} {ys:<12.2f} {status}")
        
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
