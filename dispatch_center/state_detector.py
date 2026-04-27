#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
状态识别器 - 缆机与车辆的状态精确识别

=== 缆机状态识别 ===
坐标系说明：
- 装料平台区：latitude 50-150（低纬度）
- 卸料平台区：latitude 280-450（高纬度）
- xspeed > 0：向高纬度移动（向卸料区）→ 送料
- xspeed < 0：向低纬度移动（向装料区）→ 返程

缆机四种状态：
1. loading - 990平台接料
2. delivering - 送料途中  
3. unloading - 基坑卸料
4. returning - 返程途中

=== 车辆状态识别 ===
坐标系说明：
- 接料区(右端)：result_y > -400（Y值较大）
- 卸料区(左端)：result_y < -800（Y值较小）
- result_y 减小：送料方向（从右端向左端）
- result_y 增大：返程方向（从左端向右端）

车辆四种状态：
1. loading - 接料区装料
2. delivering - 送料途中
3. unloading - 卸料区卸料
4. returning - 返程途中
"""

# ==================== 缆机位置区域定义 ====================
LOADING_ZONE = (50, 150)      # 990平台接料区
UNLOADING_ZONE = (280, 450)   # 基坑卸料区
TRANSIT_ZONE = (150, 280)     # 中途区域

# 缆机速度阈值
SPEED_THRESHOLD = 0.5         # 速度判定阈值

# ==================== 车辆位置区域定义 ====================
VEHICLE_LOADING_ZONE = (-400, 0)       # 接料区(右端)：result_y > -400
VEHICLE_UNLOADING_ZONE = (-2000, -800) # 卸料区(左端)：result_y < -800
VEHICLE_TRANSIT_ZONE = (-800, -400)    # 途中区域

# 车辆速度阈值
VEHICLE_SPEED_THRESHOLD = 0.5          # 车辆速度判定阈值
VEHICLE_Y_DELTA_THRESHOLD = 10         # Y坐标变化阈值（过滤信号跳跃）


def detect_cable_car_state(latitude, xspeed, start):
    """
    检测缆机状态 - 基于位置和速度的综合判断
    
    Args:
        latitude: X坐标（纬度）
        xspeed: X方向速度（正值=向卸料区，负值=向装料区）
        start: 启动状态（0/1）
    
    Returns:
        state: 状态代码 (loading/delivering/unloading/returning/stopped)
        state_label: 状态中文标签
        location: 位置区域
    """
    # 确定位置区域
    if LOADING_ZONE[0] <= latitude <= LOADING_ZONE[1]:
        location = "装料平台区"
        location_code = "loading_zone"
    elif UNLOADING_ZONE[0] <= latitude <= UNLOADING_ZONE[1]:
        location = "卸料平台区"
        location_code = "unloading_zone"
    elif TRANSIT_ZONE[0] <= latitude < TRANSIT_ZONE[1]:
        location = "中途区域"
        location_code = "transit"
    else:
        location = "其他区域"
        location_code = "unknown"
    
    # 状态判断逻辑
    # 
    # 速度方向说明：
    # - xspeed > 0（正值）：X增加，向高纬度移动（向卸料区）→ 送料途中
    # - xspeed < 0（负值）：X减小，向低纬度移动（向装料区）→ 返程途中
    
    # 1. 990平台接料
    # 特征：在装料平台区 + 速度接近0（等待/装料中）
    if location_code == "loading_zone":
        if start == 0:
            return "loading", "990平台接料", location
        else:
            # start=1但速度很低，可能是刚开始移动或调整位置
            if abs(xspeed) < SPEED_THRESHOLD:
                return "loading", "990平台接料", location
            elif xspeed > SPEED_THRESHOLD:
                # 在装料区但向卸料方向移动（X增加），说明刚装好料出发去送料
                return "delivering", "送料途中", location
            else:
                return "loading", "990平台接料", location
    
    # 2. 基坑卸料
    # 特征：在卸料平台区 + 速度接近0（卸料中）
    if location_code == "unloading_zone":
        if start == 0:
            return "unloading", "基坑卸料", location
        else:
            # start=1但速度很低，可能是卸料中或调整位置
            if abs(xspeed) < SPEED_THRESHOLD:
                return "unloading", "基坑卸料", location
            elif xspeed < -SPEED_THRESHOLD:
                # 在卸料区但向装料方向移动（X减小），说明卸完料开始返程
                return "returning", "返程途中", location
            else:
                return "unloading", "基坑卸料", location
    
    # 3. 中途区域判断
    # 特征：在中途区域，根据速度方向判断
    if location_code == "transit":
        if xspeed > SPEED_THRESHOLD:
            # X增加，向高纬度移动 → 向卸料区 → 送料途中
            return "delivering", "送料途中", location
        elif xspeed < -SPEED_THRESHOLD:
            # X减小，向低纬度移动 → 向装料区 → 返程途中
            return "returning", "返程途中", location
        else:
            # 中途停止或低速，根据start判断
            return "delivering" if start == 1 else "stopped", "送料途中" if start == 1 else "停止", location
    
    # 4. 其他区域的判断
    if location_code == "unknown":
        # 根据速度方向判断
        if xspeed > SPEED_THRESHOLD:
            # X增加，向卸料区移动 → 送料
            return "delivering", "送料途中", location
        elif xspeed < -SPEED_THRESHOLD:
            # X减小，向装料区移动 → 返程
            return "returning", "返程途中", location
        else:
            return "stopped", "停止", location
    
    return "stopped", "停止", location


def detect_vehicle_state(result_y, speed, y_trend=0):
    """
    检测车辆状态 - 基于位置、速度和Y坐标趋势的综合判断
    
    Args:
        result_y: Y坐标（负值，右端约-338，左端约-1000）
        speed: 车辆速度
        y_trend: Y坐标变化趋势（滑动窗口计算的累计变化量）
                 y_trend < 0: Y减小 → 送料方向
                 y_trend > 0: Y增大 → 返程方向
    
    Returns:
        state: 状态代码 (loading/delivering/unloading/returning/stopped)
        state_label: 状态中文标签
        location: 位置区域
    """
    if VEHICLE_LOADING_ZONE[0] <= result_y <= VEHICLE_LOADING_ZONE[1]:
        location = "接料区(右端)"
        location_code = "loading_zone"
    elif VEHICLE_UNLOADING_ZONE[0] <= result_y <= VEHICLE_UNLOADING_ZONE[1]:
        location = "卸料区(左端)"
        location_code = "unloading_zone"
    elif VEHICLE_TRANSIT_ZONE[0] <= result_y < VEHICLE_TRANSIT_ZONE[1]:
        location = "途中区域"
        location_code = "transit"
    else:
        location = "其他区域"
        location_code = "unknown"

    is_moving = speed is not None and float(speed) > VEHICLE_SPEED_THRESHOLD
    has_trend = abs(y_trend) > VEHICLE_Y_DELTA_THRESHOLD

    if location_code == "loading_zone":
        if not is_moving:
            return "loading", "接料区装料", location
        else:
            if has_trend and y_trend < -VEHICLE_Y_DELTA_THRESHOLD:
                return "delivering", "送料途中", location
            elif has_trend and y_trend > VEHICLE_Y_DELTA_THRESHOLD:
                return "returning", "返程途中", location
            else:
                return "loading", "接料区装料", location

    if location_code == "unloading_zone":
        if not is_moving:
            return "unloading", "卸料区卸料", location
        else:
            if has_trend and y_trend > VEHICLE_Y_DELTA_THRESHOLD:
                return "returning", "返程途中", location
            elif has_trend and y_trend < -VEHICLE_Y_DELTA_THRESHOLD:
                return "delivering", "送料途中", location
            else:
                return "unloading", "卸料区卸料", location

    if location_code == "transit":
        if has_trend and y_trend < -VEHICLE_Y_DELTA_THRESHOLD:
            return "delivering", "送料途中", location
        elif has_trend and y_trend > VEHICLE_Y_DELTA_THRESHOLD:
            return "returning", "返程途中", location
        else:
            if is_moving:
                return "delivering", "送料途中", location
            else:
                return "stopped", "停止", location

    if location_code == "unknown":
        if has_trend and y_trend < -VEHICLE_Y_DELTA_THRESHOLD:
            return "delivering", "送料途中", location
        elif has_trend and y_trend > VEHICLE_Y_DELTA_THRESHOLD:
            return "returning", "返程途中", location
        elif is_moving:
            return "delivering", "送料途中", location
        else:
            return "stopped", "停止", location

    return "stopped", "停止", location


def get_state_color(state):
    """获取状态对应的颜色"""
    colors = {
        "loading": "#ffd93d",      # 黄色 - 接料中
        "delivering": "#00d4ff",   # 蓝色 - 送料中
        "unloading": "#ff6b6b",    # 红色 - 卸料中
        "returning": "#00ff88",    # 绿色 - 返程中
        "stopped": "#5a6380",      # 灰色 - 停止
    }
    return colors.get(state, "#8b92b4")


def get_state_icon(state):
    """获取状态对应的图标"""
    icons = {
        "loading": "⏳",      # 等待/装料
        "delivering": "🚚",   # 运输
        "unloading": "📦",    # 卸货
        "returning": "🔙",    # 返回
        "stopped": "⏹️",      # 停止
    }
    return icons.get(state, "❓")


# 测试代码
if __name__ == '__main__':
    # 测试用例说明：
    # - latitude: 低值(50-150)=装料区, 高值(280-450)=卸料区
    # - xspeed > 0: X增加，向卸料区移动（送料）
    # - xspeed < 0: X减小，向装料区移动（返程）
    
    test_cases = [
        # (cable_id, latitude, xspeed, start, expected_state, description)
        (1, 377.80, 0.00, 1, "unloading", "在卸料区，停止 → 卸料中"),
        (2, 424.00, 0.00, 1, "unloading", "在卸料区，停止 → 卸料中"),
        (3, 67.80, 0.00, 0, "loading", "在装料区，停止 → 接料中"),
        
        # 运动状态测试
        (4, 100.00, 5.0, 1, "delivering", "在装料区，xspeed>0 → 刚出发送料（向卸料区）"),
        (5, 350.00, -5.0, 1, "returning", "在卸料区，xspeed<0 → 卸完返程（向装料区）"),
        (6, 200.00, 4.0, 1, "delivering", "在中途，xspeed>0 → 送料途中（向卸料区）"),
        (7, 200.00, -4.0, 1, "returning", "在中途，xspeed<0 → 返程途中（向装料区）"),
    ]
    
    print("=" * 100)
    print("缆机状态识别测试 - 修正版（速度方向已修正）")
    print("=" * 100)
    print("\n坐标系说明：")
    print("  - 装料平台区：latitude 50-150（低纬度）")
    print("  - 卸料平台区：latitude 280-450（高纬度）")
    print("  - xspeed > 0：X增加，向高纬度移动 → 送料途中")
    print("  - xspeed < 0：X减小，向低纬度移动 → 返程途中")
    print("=" * 100)
    
    print(f"\n{'ID':<4} {'位置':<8} {'速度':<8} {'启动':<4} {'状态':<12} {'标签':<12} {'区域':<10} {'结果'}")
    print("-" * 100)
    
    all_pass = True
    for cable_id, lat, xs, st, expected, desc in test_cases:
        state, label, location = detect_cable_car_state(lat, xs, st)
        match = "✓" if state == expected else f"✗"
        if state != expected:
            all_pass = False
            match += f"(应为{expected})"
        print(f"{cable_id:<4} {lat:<8.1f} {xs:<+8.1f} {st:<4} {state:<12} {label:<12} {location:<10} {match}")
        print(f"     {desc}")
    
    print("-" * 100)
    if all_pass:
        print("\n✅ 所有测试用例通过！")
    else:
        print("\n❌ 部分测试用例失败！")
    print("=" * 100)
