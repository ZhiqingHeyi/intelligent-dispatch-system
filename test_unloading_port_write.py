#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 vehicle_system.data 表的 unloading_port 写入功能
"""

import pymysql
import sys

# 数据库配置（与 config.py 一致）
VEHICLE_DB = {
    'host': '192.168.1.88',
    'port': 3306,
    'user': 'root',
    'password': '!Tmhc20170717',
    'database': 'vehicle_system',
    'charset': 'utf8mb4'
}


def test_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("步骤1: 测试数据库连接")
    print("=" * 60)
    try:
        conn = pymysql.connect(**VEHICLE_DB)
        print(f"✅ 数据库连接成功")
        print(f"   主机: {VEHICLE_DB['host']}")
        print(f"   数据库: {VEHICLE_DB['database']}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


def check_table_structure():
    """查看 data 表结构"""
    print("\n" + "=" * 60)
    print("步骤2: 查看 data 表结构")
    print("=" * 60)
    try:
        conn = pymysql.connect(**VEHICLE_DB)
        cursor = conn.cursor()
        cursor.execute("DESCRIBE data")
        rows = cursor.fetchall()
        print("\n表结构:")
        print(f"{'字段名':<20} {'类型':<20} {'可空':<10}")
        print("-" * 50)
        for row in rows:
            print(f"{row[0]:<20} {row[1]:<20} {row[2]:<10}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ 查询表结构失败: {e}")
        return False


def query_current_data(tid=None):
    """查询当前 data 表数据"""
    print("\n" + "=" * 60)
    print("步骤3: 查询当前 data 表数据")
    print("=" * 60)
    try:
        conn = pymysql.connect(**VEHICLE_DB)
        cursor = conn.cursor()
        
        if tid:
            cursor.execute("SELECT tid, receiving_port, unloading_port FROM data WHERE tid = %s", (tid,))
        else:
            cursor.execute("SELECT tid, receiving_port, unloading_port FROM data LIMIT 10")
        
        rows = cursor.fetchall()
        print(f"\n查询结果 ({len(rows)} 条记录):")
        print(f"{'tid':<10} {'receiving_port':<15} {'unloading_port':<15}")
        print("-" * 40)
        for row in rows:
            tid_val = row[0]
            recv_port = row[1] if row[1] is not None else 'NULL'
            unload_port = row[2] if row[2] is not None else 'NULL'
            print(f"{tid_val:<10} {recv_port:<15} {unload_port:<15}")
        
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"❌ 查询数据失败: {e}")
        return None


def test_write_unloading_port(tid, cable_car_id):
    """测试写入 unloading_port"""
    print("\n" + "=" * 60)
    print(f"步骤4: 测试写入 unloading_port (tid={tid}, cable_car_id={cable_car_id})")
    print("=" * 60)
    try:
        conn = pymysql.connect(**VEHICLE_DB)
        cursor = conn.cursor()
        
        # 写入前查询
        cursor.execute("SELECT unloading_port FROM data WHERE tid = %s", (tid,))
        before = cursor.fetchone()
        if before:
            print(f"写入前: unloading_port = {before[0] if before[0] is not None else 'NULL'}")
        else:
            print(f"⚠️ 警告: tid={tid} 的记录不存在")
        
        # 执行写入
        cursor.execute(
            'UPDATE data SET unloading_port = %s WHERE tid = %s',
            (cable_car_id, tid)
        )
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"✅ [DB-WRITE] 车辆{tid}的unloading_port设置为{cable_car_id}号缆机")
        else:
            print(f"⚠️ [DB-WRITE-WARN] 车辆{tid}在data表中不存在，无法更新")
        
        # 写入后查询验证
        cursor.execute("SELECT unloading_port FROM data WHERE tid = %s", (tid,))
        after = cursor.fetchone()
        if after:
            print(f"写入后: unloading_port = {after[0] if after[0] is not None else 'NULL'}")
            if after[0] == cable_car_id:
                print("✅ 验证成功: 数据已正确写入")
            else:
                print("❌ 验证失败: 数据写入异常")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ [DB-WRITE-ERROR] 更新失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_clear_unloading_port(tid):
    """测试清空 unloading_port（设置为0，因为字段是NOT NULL）"""
    print("\n" + "=" * 60)
    print(f"步骤5: 测试清空 unloading_port (tid={tid}) - 设置为0")
    print("=" * 60)
    try:
        conn = pymysql.connect(**VEHICLE_DB)
        cursor = conn.cursor()
        
        # 执行清空（设置为0，因为 unloading_port 是 NOT NULL）
        cursor.execute(
            'UPDATE data SET unloading_port = 0 WHERE tid = %s',
            (tid,)
        )
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"✅ [DB-WRITE] 车辆{tid}的unloading_port已清空(设置为0)")
        else:
            print(f"⚠️ [DB-WRITE-WARN] 车辆{tid}在data表中不存在")
        
        # 清空后查询验证
        cursor.execute("SELECT unloading_port FROM data WHERE tid = %s", (tid,))
        result = cursor.fetchone()
        if result:
            print(f"清空后: unloading_port = {result[0]}")
            if result[0] == 0:
                print("✅ 验证成功: 数据已正确清空(=0)")
            else:
                print("❌ 验证失败: 数据未清空")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ [DB-WRITE-ERROR] 清空失败: {e}")
        return False


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("vehicle_system.data 表 unloading_port 写入测试")
    print("=" * 60)
    
    # 步骤1: 测试连接
    if not test_connection():
        sys.exit(1)
    
    # 步骤2: 查看表结构
    check_table_structure()
    
    # 步骤3: 查询当前数据
    rows = query_current_data()
    
    if not rows:
        print("\n⚠️ data 表中没有数据，无法测试写入")
        sys.exit(1)
    
    # 获取第一个 tid 进行测试
    test_tid = rows[0][0]
    test_cable_id = 3  # 假设的缆机ID
    
    # 步骤4: 测试写入
    test_write_unloading_port(test_tid, test_cable_id)
    
    # 步骤5: 查询验证
    query_current_data(test_tid)
    
    # 步骤6: 测试清空
    test_clear_unloading_port(test_tid)
    
    # 步骤7: 最终查询
    query_current_data(test_tid)
    
    print("\n" + "=" * 60)
    print("测试完成！请登录数据库验证:")
    print(f"  mysql -h {VEHICLE_DB['host']} -u {VEHICLE_DB['user']} -p")
    print(f"  USE {VEHICLE_DB['database']};")
    print(f"  SELECT * FROM data WHERE tid = {test_tid};")
    print("=" * 60)
