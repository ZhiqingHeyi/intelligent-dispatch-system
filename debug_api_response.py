#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API响应调试工具 - 检查返回给前端的数据
"""

import sqlite3
import json
from flask import Flask, jsonify
import sys
sys.path.insert(0, 'dispatch_center')

from database import get_db
from config import CONCRETE_GRADES

app = Flask(__name__)

@app.route('/api/status')
def get_status():
    """复制app.py中的get_status逻辑"""
    db = get_db()
    cable_cars = [dict(row) for row in db.execute('SELECT * FROM cable_cars ORDER BY id').fetchall()]
    vehicles = [dict(row) for row in db.execute('SELECT * FROM vehicles ORDER BY tid').fetchall()]
    db.close()
    
    # 打印车辆状态分布
    state_count = {}
    for v in vehicles:
        state = v.get('state', 'NULL')
        state_count[state] = state_count.get(state, 0) + 1
    
    print(f"\n【API响应】车辆state分布: {state_count}")
    print(f"【API响应】返回车辆数: {len(vehicles)}")
    
    # 检查是否有delivering状态
    delivering_vehicles = [v for v in vehicles if v.get('state') == 'delivering']
    if delivering_vehicles:
        print(f"⚠️ 【警告】发现{len(delivering_vehicles)}辆车state=delivering:")
        for v in delivering_vehicles:
            print(f"   - {v['name']}: state={v['state']}, state_label={v.get('state_label')}, location={v.get('location')}")
    
    return jsonify({
        'cable_cars': cable_cars,
        'vehicles': vehicles,
        'grades': CONCRETE_GRADES,
        'active_tasks': [],
        'recent_tasks': []
    })

if __name__ == '__main__':
    print("API调试服务器启动，访问 http://localhost:5002/api/status 查看响应数据")
    print("按Ctrl+C停止")
    app.run(host='0.0.0.0', port=5002, debug=False)
