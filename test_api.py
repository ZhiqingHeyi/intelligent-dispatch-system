#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试API返回的数据"""

import sys
sys.path.insert(0, 'dispatch_center')

from database import get_db
from config import CONCRETE_GRADES

def test_api_response():
    db = get_db()
    
    # 模拟 app.py 中的 get_status
    cable_cars = [dict(row) for row in db.execute('SELECT * FROM cable_cars ORDER BY id').fetchall()]
    vehicles = [dict(row) for row in db.execute('SELECT * FROM vehicles ORDER BY tid').fetchall()]
    
    print("=" * 80)
    print("API /api/status 返回的车辆数据:")
    print("=" * 80)
    
    for v in vehicles:
        print(f"\n车辆 {v['name']} (tid={v['tid']}):")
        print(f"  - id: {v['id']}")
        print(f"  - status: {v['status']}")
        print(f"  - direction: {v['direction']}")
        print(f"  - state: {v['state']}")
        print(f"  - state_label: {v['state_label']}")
        print(f"  - location: {v['location']}")
        print(f"  - result_y: {v['result_y']}")
        print(f"  - speed: {v['speed']}")
    
    db.close()

if __name__ == '__main__':
    test_api_response()
