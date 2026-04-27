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
坐标系说明（基于实测数据校准）：
- 接料区(右端)：result_y > 0（Y值约 0~400，如6号车=87）
- 卸料区(左端)：result_y < -800（Y值约 -800~-1400，如2号车=-1341）
- result_y 减小：送料方向（从右端向左端，87 → -1341）
- result_y 增大：返程方向（从左端向右端，-1341 → 87）

实测参考点：
- 6号车(接料区)：result_y ≈ 87
- 2号车(卸料区)：result_y ≈ -1341

车辆四种状态：
1. loading - 接料区装料
2. delivering - 送料途中
3. unloading - 卸料区卸料
4. returning - 返程途中
"""

# ==================== 缆机位置区域定义 ====================
# 优化说明：将LOADING_ZONE下限从50放宽到40，覆盖990平台休息区
# 2号缆机实测位置latitude=49.80，在平台休息区，需要被识别为装料区
LOADING_ZONE = (40, 150)      # 990平台接料区（含休息区，原50→40）
UNLOADING_ZONE = (280, 450)   # 基坑卸料区
TRANSIT_ZONE = (150, 280)     # 中途区域

# 缆机速度阈值
SPEED_THRESHOLD = 0.5         # 速度判定阈值

# ==================== 车辆位置区域定义 ====================
# 基于实测数据精确校准（2026-04-27）
# 实测运行数据：
# - 接料区：Y ≈ 87（装料等待）
# - 送料途中（可匹配）：Y 从 87 减小到 0 ~ -900
# - 卸料区：Y < -1100（典型值 -1200~-1300，卸料等待）
# - 返程：Y 从 -1200~-1300 增大回到 0~87
VEHICLE_LOADING_ZONE = (50, 120)       # 接料区：Y > 50（典型值87）
VEHICLE_DELIVERING_ZONE = (-950, 50)   # 送料途中/可匹配区：0 ~ -900，可入队匹配
VEHICLE_UNLOADING_ZONE = (-1400, -950) # 卸料区：Y < -950（典型值-1100以下）

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


def detect_vehicle_state(result_y, speed, y_trend=0, direction='idle'):
    """
    检测车辆状态 - 基于位置、速度和方向的综合判断（方案A）
    
    Args:
        result_y: Y坐标（接料区约87，卸料区约-1200~-1300）
        speed: 车辆速度
        y_trend: Y坐标变化趋势
        direction: 行驶方向（'going'=送料，'returning'=返程，'idle'=静止）
    
    Returns:
        state: 状态代码
        state_label: 状态中文标签
        location: 位置区域
    """
    if VEHICLE_LOADING_ZONE[0] <= result_y <= VEHICLE_LOADING_ZONE[1]:
        location = "接料区"
        location_code = "loading_zone"
    elif VEHICLE_UNLOADING_ZONE[0] <= result_y <= VEHICLE_UNLOADING_ZONE[1]:
        location = "卸料区"
        location_code = "unloading_zone"
    elif VEHICLE_DELIVERING_ZONE[0] <= result_y <= VEHICLE_DELIVERING_ZONE[1]:
        location = "送料途中"
        location_code = "delivering_zone"
    else:
        location = "其他区域"
        location_code = "unknown"

    is_moving = speed is not None and float(speed) > VEHICLE_SPEED_THRESHOLD

    # 方案A：更精确的状态识别（位置优先于方向）
    
    # 1. 接料区/停车区（Y > 50）- 最高优先级
    if location_code == "loading_zone":
        # 统一显示"待命"，不区分是等料还是停车
        return "standby", "待命", location
    
    # 2. 卸料区（Y < -950）- 第二优先级
    if location_code == "unloading_zone":
        if is_moving:
            return "unloading", "卸料中", location
        else:
            return "unloading_wait", "卸料区等待", location
    
    # 3. 送料途中（-950 < Y < 50）- 第三优先级
    if location_code == "delivering_zone":
        if direction == 'going':
            if is_moving:
                return "delivering", "送料中", location
            else:
                return "delivering_pause", "送料暂停", location
        elif direction == 'returning':
            # 明确返程中，显示返程
            return "returning", "返程中", location
        else:
            # 【Bug修复】方向不明确（idle/stopped）但在送料区间，保守显示为待命
            # 不根据is_moving判断，避免信号波动导致状态乱跳
            return "standby", "待命", location
    
    # 4. 其他区域（未知区域）- 最低优先级
    # 【Bug修复】只有在明确going且移动中才显示送料中，否则保守显示待命
    if direction == 'going' and is_moving:
        return "delivering", "送料中", location
    elif direction == 'returning':
        return "returning", "返程中", location
    else:
        return "standby", "待命", location


def get_state_color(state):
    """获取状态对应的颜色（方案A）"""
    colors = {
        "standby": "#ffd93d",          # 黄色 - 待命（接料区/停车区）
        "delivering": "#00d4ff",       # 蓝色 - 送料中
        "delivering_pause": "#5a8cff", # 浅蓝色 - 送料暂停
        "unloading": "#ff6b6b",        # 红色 - 卸料中
        "unloading_wait": "#ff9f9f",   # 粉红色 - 卸料区等待
        "returning": "#00ff88",        # 绿色 - 返程中
        "loading": "#ffd93d",          # 兼容旧状态
        "stopped": "#5a6380",          # 灰色 - 停止
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
    print("=" * 100)
    print("缆机状态识别测试 - 修正版（速度方向已修正，阈值已优化）")
    print("=" * 100)
    
    # ========== 缆机测试 ==========
    print("\n【缆机状态测试】")
    cable_cases = [
        # (cable_id, latitude, xspeed, start, expected_state, description)
        (1, 377.80, 0.00, 1, "unloading", "在卸料区，停止 → 卸料中"),
        (2, 424.00, 0.00, 1, "unloading", "在卸料区，停止 → 卸料中"),
        (3, 67.80, 0.00, 0, "loading", "在装料区，停止 → 接料中"),
        (4, 100.00, 5.0, 1, "delivering", "在装料区，xspeed>0 → 刚出发送料"),
        (5, 350.00, -5.0, 1, "returning", "在卸料区，xspeed<0 → 卸完返程"),
        (6, 200.00, 4.0, 1, "delivering", "在中途，xspeed>0 → 送料途中"),
        (7, 200.00, -4.0, 1, "returning", "在中途，xspeed<0 → 返程途中"),
        (8, 49.80, 0.00, 0, "loading", "2号缆机实际位置 → 990平台接料"),
        (9, 45.00, 0.00, 0, "loading", "边界测试：latitude=45.00 → 装料区"),
    ]
    
    print(f"\n{'ID':<4} {'位置':<8} {'速度':<8} {'启动':<4} {'状态':<12} {'标签':<12} {'区域':<10} {'结果'}")
    print("-" * 100)
    
    all_pass = True
    for cable_id, lat, xs, st, expected, desc in cable_cases:
        state, label, location = detect_cable_car_state(lat, xs, st)
        match = "✓" if state == expected else f"✗"
        if state != expected:
            all_pass = False
            match += f"(应为{expected})"
        print(f"{cable_id:<4} {lat:<8.1f} {xs:<+8.1f} {st:<4} {state:<12} {label:<12} {location:<10} {match}")
        print(f"     {desc}")
    
    # ========== 车辆状态测试（Bug修复验证） ==========
    print("\n" + "=" * 100)
    print("【车辆状态测试 - Bug修复验证】")
    print("=" * 100)
    print("车辆位置区域：接料区Y>50，送料途中-950<Y<50，卸料区Y<-950")
    print("=" * 100)
    
    vehicle_cases = [
        # (result_y, speed, y_trend, direction, expected_state, description)
        # 接料区测试
        (87, 0, 0, 'stopped', 'standby', "接料区，停止 → 待命"),
        (87, 5, 0, 'going', 'standby', "接料区，移动 → 待命（接料区统一显示待命）"),
        
        # 送料途中 - 关键bug修复测试
        (-500, 10, -50, 'going', 'delivering', "送料途中，direction=going，移动 → 送料中"),
        (-500, 0, 0, 'going', 'delivering_pause', "送料途中，direction=going，停止 → 送料暂停"),
        (-500, 10, 0, 'idle', 'standby', "【Bug修复】送料途中，direction=idle，移动 → 待命（不盲目显示送料中）"),
        (-500, 0, 0, 'idle', 'standby', "【Bug修复】送料途中，direction=idle，停止 → 待命"),
        (-500, 10, 0, 'returning', 'returning', "送料途中，direction=returning，移动 → 返程中"),
        
        # 卸料区测试
        (-1200, 0, 0, 'stopped', 'unloading_wait', "卸料区，停止 → 卸料区等待"),
        (-1200, 5, 0, 'returning', 'unloading', "卸料区，返程中移动 → 卸料中"),
        
        # 未知区域测试
        (2000, 10, 0, 'idle', 'standby', "【Bug修复】未知区域，direction=idle，移动 → 待命（不盲目显示送料中）"),
    ]
    
    print(f"\n{'Y坐标':<10} {'速度':<8} {'方向':<10} {'预期状态':<12} {'实际状态':<12} {'标签':<12} {'结果'}")
    print("-" * 100)
    
    for result_y, speed, y_trend, direction, expected, desc in vehicle_cases:
        state, label, location = detect_vehicle_state(result_y, speed, y_trend, direction)
        match = "✓" if state == expected else f"✗"
        if state != expected:
            all_pass = False
            match += f"(应为{expected})"
        print(f"{result_y:<10} {speed:<8} {direction:<10} {expected:<12} {state:<12} {label:<12} {match}")
        print(f"     {desc}")
    
    print("-" * 100)
    if all_pass:
        print("\n✅ 所有测试用例通过！Bug已修复！")
    else:
        print("\n❌ 部分测试用例失败！")
    print("=" * 100)
