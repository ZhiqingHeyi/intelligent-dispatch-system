#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整同步测试 - 模拟data_sync中的车辆状态检测
"""

import sys
sys.path.insert(0, 'dispatch_center')

from state_detector import detect_vehicle_state
from collections import deque

# 模拟车辆数据
test_vehicles = [
    {'tid': 1, 'result_y': 87, 'speed': 5, 'desc': '接料区移动中'},
    {'tid': 2, 'result_y': 87, 'speed': 0, 'desc': '接料区停止'},
    {'tid': 3, 'result_y': -500, 'speed': 10, 'desc': '送料途中移动'},
    {'tid': 4, 'result_y': -1200, 'speed': 0, 'desc': '卸料区停止'},
]

# 模拟Y坐标历史
_vehicle_y_history = {}

def simulate_direction_detection(tid, result_y, speed):
    """模拟方向检测"""
    if tid not in _vehicle_y_history:
        _vehicle_y_history[tid] = deque(maxlen=5)
    
    history = _vehicle_y_history[tid]
    history.append(result_y)
    
    if speed < 0.1:
        return 'stopped'
    
    if len(history) < 2:
        return 'idle'
    
    # 计算趋势
    y_trend = sum(list(history)[i] - list(history)[i-1] for i in range(1, len(history)))
    
    if y_trend < -10:
        return 'going'
    elif y_trend > 10:
        return 'returning'
    return 'idle'

print("=" * 80)
print("车辆状态同步测试")
print("=" * 80)

print(f"\n{'TID':<5} {'Y坐标':<10} {'速度':<8} {'描述':<15} {'direction':<10} {'state':<15} {'state_label':<12}")
print("-" * 80)

for v in test_vehicles:
    # 模拟多次添加Y坐标来建立历史
    for _ in range(3):
        direction = simulate_direction_detection(v['tid'], v['result_y'], v['speed'])
    
    # 计算趋势
    history = _vehicle_y_history.get(v['tid'], deque(maxlen=5))
    y_trend = sum(list(history)[i] - list(history)[i-1] for i in range(1, len(history))) if len(history) >= 2 else 0
    
    # 检测状态
    state, state_label, location = detect_vehicle_state(v['result_y'], v['speed'], y_trend, direction)
    
    print(f"{v['tid']:<5} {v['result_y']:<10.0f} {v['speed']:<8.1f} {v['desc']:<15} {direction:<10} {state:<15} {state_label:<12}")
    
    # 检查不一致
    if direction == 'going' and state != 'delivering' and state != 'delivering_pause':
        if v['result_y'] <= 50 and v['result_y'] >= -950:
            print(f"  ⚠️  不一致：direction=going 但 state={state}（送料途中区域应显示送料中）")
        elif v['result_y'] > 50:
            print(f"  ℹ️  不一致但合理：direction=going 但 Y={v['result_y']}>50（接料区），state={state}")

print("=" * 80)
