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

=== 车辆状态识别（带状态锁定机制）===
核心设计：状态一旦确认就锁定，只有明确的转换条件才能变更
- 解决GPS信号不稳定导致状态频繁跳变的问题
- 状态转换需要满足明确的条件（位置+方向双重确认）

状态流转：
  standby → delivering:  车辆离开接料区(Y<50) + 方向going
  delivering → unloading: 车辆到达卸料区(Y<-950)
  unloading → returning: 车辆离开卸料区 + 方向returning
  returning → standby:   车辆回到接料区(Y>50)
"""

# ==================== 缆机位置区域定义 ====================
LOADING_ZONE = (40, 150)
UNLOADING_ZONE = (280, 450)
TRANSIT_ZONE = (150, 280)

SPEED_THRESHOLD = 0.5

# ==================== 车辆位置区域定义 ====================
VEHICLE_LOADING_ZONE = (50, 120)
VEHICLE_DELIVERING_ZONE = (-950, 50)
VEHICLE_UNLOADING_ZONE = (-1400, -950)

VEHICLE_SPEED_THRESHOLD = 0.5
VEHICLE_Y_DELTA_THRESHOLD = 10

# ==================== 车辆状态锁定机制 ====================
_vehicle_locked_state = {}
_vehicle_state_confirm_count = {}
STATE_CONFIRM_THRESHOLD = 3


def _can_transition(current_state, new_raw_state, location_code, direction):
    """
    判断状态是否允许转换 - 状态锁定核心逻辑
    
    关键原则：
    - standby 只能转到 delivering（车辆开始送料）
    - delivering 只能转到 unloading（车辆到达卸料区）
    - unloading 只能转到 returning（车辆开始返程）
    - returning 只能转到 standby（车辆回到接料区）
    - 其他转换一律不允许（锁定当前状态）
    
    每个转换都需要位置+方向的双重确认
    """
    TRANSITIONS = {
        'standby': ['delivering'],
        'delivering': ['unloading', 'unloading_wait', 'returning', 'delivering_pause'],
        'delivering_pause': ['delivering', 'unloading', 'unloading_wait', 'returning'],
        'unloading': ['returning', 'unloading_wait'],
        'unloading_wait': ['returning', 'unloading'],
        'returning': ['standby'],
    }
    
    allowed = TRANSITIONS.get(current_state, [])
    
    if new_raw_state not in allowed:
        return False
    
    # 额外条件：转换需要位置确认
    if current_state == 'standby' and new_raw_state == 'delivering':
        if location_code != 'delivering_zone' and location_code != 'unloading_zone':
            return False
        if direction != 'going':
            return False
    
    if current_state == 'delivering' and new_raw_state == 'unloading':
        if location_code != 'unloading_zone':
            return False
    
    if current_state == 'delivering_pause' and new_raw_state == 'delivering':
        if direction != 'going':
            return False
    
    if current_state in ('unloading', 'unloading_wait') and new_raw_state == 'returning':
        if direction != 'returning' and location_code == 'unloading_zone':
            return False
    
    if current_state == 'returning' and new_raw_state == 'standby':
        if location_code != 'loading_zone':
            return False
    
    return True


def detect_vehicle_state_locked(tid, result_y, speed, y_trend=0, direction='idle'):
    """
    带状态锁定的车辆状态检测
    
    核心逻辑：
    1. 先根据位置+方向计算"原始状态"（raw_state）
    2. 查看当前锁定状态（locked_state）
    3. 如果 raw_state 与 locked_state 不同，检查是否允许转换
    4. 允许转换需要连续N帧确认，防止信号波动误触发
    5. 不允许转换则保持当前锁定状态
    """
    # 计算位置区域
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

    # Step 1: 计算原始状态（基于当前帧数据）
    if location_code == "loading_zone":
        raw_state, raw_label = "standby", "待命"
    elif location_code == "unloading_zone":
        if is_moving and direction == 'returning':
            raw_state, raw_label = "returning", "返程中"
        elif is_moving:
            raw_state, raw_label = "unloading", "卸料中"
        else:
            raw_state, raw_label = "unloading_wait", "卸料区等待"
    elif location_code == "delivering_zone":
        if direction == 'going':
            if is_moving:
                raw_state, raw_label = "delivering", "送料中"
            else:
                raw_state, raw_label = "delivering_pause", "送料暂停"
        elif direction == 'returning':
            raw_state, raw_label = "returning", "返程中"
        else:
            raw_state, raw_label = "standby", "待命"
    else:
        if direction == 'going' and is_moving:
            raw_state, raw_label = "delivering", "送料中"
        elif direction == 'returning':
            raw_state, raw_label = "returning", "返程中"
        else:
            raw_state, raw_label = "standby", "待命"

    # Step 2: 获取当前锁定状态
    locked = _vehicle_locked_state.get(tid)
    
    if locked is None:
        # 首次检测，直接锁定原始状态
        _vehicle_locked_state[tid] = raw_state
        _vehicle_state_confirm_count[tid] = 0
        return raw_state, raw_label, location

    # Step 3: 如果原始状态与锁定状态相同，直接返回
    if raw_state == locked:
        _vehicle_state_confirm_count[tid] = 0
        state_labels = {
            'standby': '待命', 'delivering': '送料中', 'delivering_pause': '送料暂停',
            'unloading': '卸料中', 'unloading_wait': '卸料区等待', 'returning': '返程中',
        }
        return locked, state_labels.get(locked, raw_label), location

    # Step 4: 检查是否允许转换
    if not _can_transition(locked, raw_state, location_code, direction):
        # 不允许转换，保持锁定状态
        _vehicle_state_confirm_count[tid] = 0
        state_labels = {
            'standby': '待命', 'delivering': '送料中', 'delivering_pause': '送料暂停',
            'unloading': '卸料中', 'unloading_wait': '卸料区等待', 'returning': '返程中',
        }
        return locked, state_labels.get(locked, '未知'), location

    # Step 5: 允许转换，但需要连续确认
    confirm_key = f"{tid}_{locked}_{raw_state}"
    if confirm_key not in _vehicle_state_confirm_count:
        _vehicle_state_confirm_count[confirm_key] = 0

    if _vehicle_state_confirm_count[confirm_key] >= STATE_CONFIRM_THRESHOLD:
        # 确认次数达到阈值，执行状态转换
        _vehicle_locked_state[tid] = raw_state
        # 清除该车辆所有旧的确认计数
        keys_to_delete = [k for k in list(_vehicle_state_confirm_count.keys())
                          if isinstance(k, str) and k.startswith(f"{tid}_")]
        for k in keys_to_delete:
            del _vehicle_state_confirm_count[k]
        return raw_state, raw_label, location
    else:
        # 还在确认中，增加计数并保持锁定状态
        _vehicle_state_confirm_count[confirm_key] += 1
        state_labels = {
            'standby': '待命', 'delivering': '送料中', 'delivering_pause': '送料暂停',
            'unloading': '卸料中', 'unloading_wait': '卸料区等待', 'returning': '返程中',
        }
        return locked, state_labels.get(locked, '未知'), location


def force_unlock_vehicle_state(tid, new_state=None):
    """强制解锁车辆状态（用于手动设置状态等场景）"""
    if new_state:
        _vehicle_locked_state[tid] = new_state
    elif tid in _vehicle_locked_state:
        del _vehicle_locked_state[tid]
    # 清除所有确认计数
    keys_to_delete = [k for k in _vehicle_state_confirm_count if k.startswith(f"{tid}_")]
    for k in keys_to_delete:
        del _vehicle_state_confirm_count[k]


def get_vehicle_locked_state(tid):
    """获取车辆当前锁定状态"""
    return _vehicle_locked_state.get(tid)


def detect_cable_car_state(latitude, xspeed, start):
    """
    检测缆机状态 - 基于位置和速度的综合判断
    """
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

    if location_code == "loading_zone":
        if start == 0:
            return "loading", "990平台接料", location
        else:
            if abs(xspeed) < SPEED_THRESHOLD:
                return "loading", "990平台接料", location
            elif xspeed > SPEED_THRESHOLD:
                return "delivering", "送料途中", location
            else:
                return "loading", "990平台接料", location

    if location_code == "unloading_zone":
        if start == 0:
            return "unloading", "基坑卸料", location
        else:
            if abs(xspeed) < SPEED_THRESHOLD:
                return "unloading", "基坑卸料", location
            elif xspeed < -SPEED_THRESHOLD:
                return "returning", "返程途中", location
            else:
                return "unloading", "基坑卸料", location

    if location_code == "transit":
        if xspeed > SPEED_THRESHOLD:
            return "delivering", "送料途中", location
        elif xspeed < -SPEED_THRESHOLD:
            return "returning", "返程途中", location
        else:
            return "delivering" if start == 1 else "stopped", "送料途中" if start == 1 else "停止", location

    if location_code == "unknown":
        if xspeed > SPEED_THRESHOLD:
            return "delivering", "送料途中", location
        elif xspeed < -SPEED_THRESHOLD:
            return "returning", "返程途中", location
        else:
            return "stopped", "停止", location

    return "stopped", "停止", location


def detect_vehicle_state(result_y, speed, y_trend=0, direction='idle'):
    """
    车辆状态检测（无锁定版本，保留兼容）
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

    if location_code == "loading_zone":
        return "standby", "待命", location

    if location_code == "unloading_zone":
        if is_moving:
            return "unloading", "卸料中", location
        else:
            return "unloading_wait", "卸料区等待", location

    if location_code == "delivering_zone":
        if direction == 'going':
            if is_moving:
                return "delivering", "送料中", location
            else:
                return "delivering_pause", "送料暂停", location
        elif direction == 'returning':
            return "returning", "返程中", location
        else:
            return "standby", "待命", location

    if direction == 'going' and is_moving:
        return "delivering", "送料中", location
    elif direction == 'returning':
        return "returning", "返程中", location
    else:
        return "standby", "待命", location


def get_state_color(state):
    colors = {
        "standby": "#ffd93d",
        "delivering": "#00d4ff",
        "delivering_pause": "#5a8cff",
        "unloading": "#ff6b6b",
        "unloading_wait": "#ff9f9f",
        "returning": "#00ff88",
        "loading": "#ffd93d",
        "stopped": "#5a6380",
    }
    return colors.get(state, "#8b92b4")


def get_state_icon(state):
    icons = {
        "loading": "⏳",
        "delivering": "🚚",
        "unloading": "📦",
        "returning": "🔙",
        "stopped": "⏹️",
    }
    return icons.get(state, "❓")


# 测试代码
if __name__ == '__main__':
    print("=" * 100)
    print("状态识别测试 - 带状态锁定机制")
    print("=" * 100)

    # ========== 车辆状态锁定测试 ==========
    print("\n【车辆状态锁定测试】")
    print("模拟GPS信号不稳定场景：车辆在送料中，但GPS偶尔跳到接料区")
    print("=" * 100)

    # 重置锁定状态
    _vehicle_locked_state.clear()
    _vehicle_state_confirm_count.clear()

    # 模拟一个完整的送料周期
    test_sequence = [
        # (tid, result_y, speed, direction, expected_locked_state, description)
        # 阶段1: 车辆在接料区待命
        (1, 87, 0, 'stopped', 'standby', "接料区待命"),
        (1, 87, 0, 'stopped', 'standby', "接料区待命"),
        (1, 87, 0, 'stopped', 'standby', "接料区待命"),

        # 阶段2: 车辆开始送料（离开接料区，方向going）
        # 确认机制：连续3帧raw_state=delivering后锁定
        (1, 30, 5, 'going', 'standby', "离开接料区，确认计数+1(1/3)"),
        (1, -10, 5, 'going', 'standby', "确认计数+1(2/3)"),
        (1, -50, 5, 'going', 'standby', "确认计数+1(3/3)，达到阈值"),
        (1, -100, 5, 'going', 'delivering', "确认完成，锁定为送料中"),

        # 阶段3: GPS信号波动！Y坐标偶尔跳回接料区
        (1, -200, 5, 'going', 'delivering', "送料中（正常）"),
        (1, 60, 0, 'idle', 'delivering', "⚠️ GPS跳到接料区，但锁定不变！"),
        (1, -250, 5, 'going', 'delivering', "恢复，锁定仍为送料中"),
        (1, 80, 0, 'stopped', 'delivering', "⚠️ GPS又跳到接料区，锁定不变！"),
        (1, -300, 5, 'going', 'delivering', "恢复，锁定仍为送料中"),

        # 阶段4: 车辆到达卸料区
        # delivering → unloading_wait 需要确认
        (1, -1000, 0, 'stopped', 'delivering', "到达卸料区，确认计数+1(1/3)"),
        (1, -1100, 0, 'stopped', 'delivering', "确认计数+1(2/3)"),
        (1, -1200, 0, 'stopped', 'delivering', "确认计数+1(3/3)，达到阈值"),
        (1, -1200, 0, 'stopped', 'unloading_wait', "确认完成，锁定为卸料区等待"),

        # 阶段5: GPS波动在卸料区
        (1, -800, 0, 'idle', 'unloading_wait', "⚠️ GPS跳到送料区，锁定不变！"),
        (1, -1200, 0, 'stopped', 'unloading_wait', "恢复"),

        # 阶段6: 车辆开始返程
        # unloading_wait → returning 需要确认
        (1, -1100, 5, 'returning', 'unloading_wait', "开始返程，确认计数+1(1/3)"),
        (1, -900, 5, 'returning', 'unloading_wait', "确认计数+1(2/3)"),
        (1, -700, 5, 'returning', 'unloading_wait', "确认计数+1(3/3)，达到阈值"),
        (1, -500, 5, 'returning', 'returning', "确认完成，锁定为返程中"),

        # 阶段7: 返程途中GPS波动
        (1, -300, 5, 'returning', 'returning', "返程中（正常）"),
        (1, -100, 0, 'idle', 'returning', "⚠️ GPS跳到送料区，锁定不变！"),
        (1, -200, 5, 'returning', 'returning', "恢复"),

        # 阶段8: 车辆回到接料区
        # returning → standby 需要确认
        (1, 60, 0, 'stopped', 'returning', "到达接料区，确认计数+1(1/3)"),
        (1, 80, 0, 'stopped', 'returning', "确认计数+1(2/3)"),
        (1, 87, 0, 'stopped', 'returning', "确认计数+1(3/3)，达到阈值"),
        (1, 87, 0, 'stopped', 'standby', "确认完成，锁定为待命"),
    ]

    print(f"\n{'帧':<4} {'Y坐标':<8} {'速度':<6} {'方向':<10} {'预期锁定':<15} {'实际状态':<15} {'标签':<10} {'结果'}")
    print("-" * 100)

    all_pass = True
    for i, (tid, y, spd, d, expected, desc) in enumerate(test_sequence):
        state, label, loc = detect_vehicle_state_locked(tid, y, spd, 0, d)
        match = "✓" if state == expected else "✗"
        if state != expected:
            all_pass = False
            match += f"(应为{expected})"
        print(f"{i+1:<4} {y:<8.0f} {spd:<6.1f} {d:<10} {expected:<15} {state:<15} {label:<10} {match} {desc}")

    print("-" * 100)
    if all_pass:
        print("\n✅ 所有测试用例通过！状态锁定机制工作正常！")
    else:
        print("\n❌ 部分测试用例失败！")
    print("=" * 100)
