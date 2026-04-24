#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析 cable_car_positions 表的结构和数据
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

def get_table_structure(cursor):
    """获取表结构"""
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
        AND TABLE_NAME = 'cable_car_positions'
        ORDER BY ORDINAL_POSITION
    """)
    return cursor.fetchall()

def get_table_stats(cursor):
    """获取表统计信息"""
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
        AND TABLE_NAME = 'cable_car_positions'
    """)
    return cursor.fetchone()

def get_sample_data(cursor, limit=10):
    """获取样例数据"""
    cursor.execute(f"SELECT * FROM cable_car_positions LIMIT {limit}")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    return columns, rows

def get_data_distribution(cursor):
    """获取数据分布统计"""
    stats = {}
    
    # 按时间统计
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            MIN(timestamp) as earliest,
            MAX(timestamp) as latest
        FROM cable_car_positions
    """)
    stats['time_range'] = cursor.fetchone()
    
    # 按cable_car_id统计
    cursor.execute("""
        SELECT 
            cableCarId,
            COUNT(*) as count
        FROM cable_car_positions
        GROUP BY cableCarId
        ORDER BY count DESC
        LIMIT 10
    """)
    stats['by_cable_car'] = cursor.fetchall()
    
    # 统计每天的记录数
    cursor.execute("""
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as count
        FROM cable_car_positions
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
        LIMIT 10
    """)
    stats['by_date'] = cursor.fetchall()
    
    return stats

def get_indexes(cursor):
    """获取表的索引信息"""
    cursor.execute("""
        SELECT 
            INDEX_NAME,
            COLUMN_NAME,
            NON_UNIQUE,
            SEQ_IN_INDEX
        FROM INFORMATION_SCHEMA.STATISTICS 
        WHERE TABLE_SCHEMA = 'cable_car' 
        AND TABLE_NAME = 'cable_car_positions'
        ORDER BY INDEX_NAME, SEQ_IN_INDEX
    """)
    return cursor.fetchall()

def format_bytes(size):
    """格式化字节大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def main():
    print("=" * 80)
    print("cable_car_positions 表分析报告")
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
        structure = get_table_structure(cursor)
        
        print(f"{'字段名':<20} {'数据类型':<15} {'长度':<10} {'允许空':<8} {'默认值':<15} {'注释':<20}")
        print("-" * 80)
        
        for col in structure:
            col_name = col[0]
            data_type = col[1]
            max_length = col[2] if col[2] else (col[3] if col[3] else '-')
            is_nullable = '是' if col[5] == 'YES' else '否'
            default = str(col[6]) if col[6] is not None else 'NULL'
            comment = col[7] if col[7] else '-'
            
            print(f"{col_name:<20} {data_type:<15} {str(max_length):<10} {is_nullable:<8} {default:<15} {comment:<20}")
        
        # 2. 表统计信息
        print("\n【表统计信息】")
        print("-" * 80)
        stats = get_table_stats(cursor)
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
        indexes = get_indexes(cursor)
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
        
        # 4. 数据分布
        print("\n【数据分布分析】")
        print("-" * 80)
        dist = get_data_distribution(cursor)
        
        if dist['time_range']:
            print(f"\n时间范围:")
            print(f"  总记录数: {dist['time_range'][0]:,} 条")
            print(f"  最早记录: {dist['time_range'][1]}")
            print(f"  最新记录: {dist['time_range'][2]}")
        
        if dist['by_cable_car']:
            print(f"\n按缆车ID统计 (Top 10):")
            print(f"{'缆车ID':<15} {'记录数':<10}")
            print("  " + "-" * 25)
            for row in dist['by_cable_car']:
                print(f"  {row[0]:<15} {row[1]:<10,}")
        
        if dist['by_date']:
            print(f"\n按日期统计 (最近10天):")
            print(f"{'日期':<15} {'记录数':<10}")
            print("  " + "-" * 25)
            for row in dist['by_date']:
                print(f"  {str(row[0]):<15} {row[1]:<10,}")
        
        # 5. 样例数据
        print("\n【样例数据】（前5条）")
        print("-" * 80)
        columns, rows = get_sample_data(cursor, 5)
        
        if rows:
            # 打印列名
            print(" | ".join(columns))
            print("-" * 80)
            
            # 打印数据
            for row in rows:
                formatted_row = []
                for val in row:
                    if val is None:
                        formatted_row.append('NULL')
                    elif isinstance(val, datetime):
                        formatted_row.append(val.strftime('%Y-%m-%d %H:%M:%S'))
                    else:
                        formatted_row.append(str(val)[:30])  # 限制长度
                print(" | ".join(formatted_row))
        else:
            print("表中暂无数据")
        
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
