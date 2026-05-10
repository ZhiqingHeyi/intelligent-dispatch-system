# 缆机运行强度智能分析系统 - 数据获取与状态判断规范

> **文档用途**: 本文档专供AI Agent构建缆机运行强度智能分析系统使用
>
> **核心目标**: 明确缆机实时数据的获取方式、数据库连接参数、状态识别算法

---

## 一、缆机数据源配置（重要！包含完整连接信息）

### 1.1 MySQL数据库连接参数

```python
CABLE_CAR_DB = {
    'host': '192.168.1.88',           # 数据库服务器IP
    'port': 3306,                      # MySQL端口
    'user': 'root',                    # 用户名
    'password': '!Tmhc20170717',       # 密码 ⚠️ 完整密码在此
    'database': 'cable_car',           # 数据库名称
    'charset': 'utf8mb4'               # 字符集
}
```

**Python连接示例**:
```python
import pymysql

def get_cable_car_connection():
    conn = pymysql.connect(
        host='192.168.1.88',
        port=3306,
        user='root',
        password='!Tmhc20170717',
        database='cable_car',
        charset='utf8mb4'
    )
    return conn
```

### 1.2 核心数据表：cable_car_status

**表结构定义**:

| 字段名 | 数据类型 | 说明 | 示例值 |
|--------|----------|------|--------|
| cable_car_id | INT | 缆机编号（1-4号） | 1, 2, 3, 4 |
| latitude | FLOAT/DOUBLE | 纬度坐标（关键位置指标） | 98.5, 320.3 |
| longitude | FLOAT/DOUBLE | 经度坐标 | 1050.2 |
| altitude | FLOAT/DOUBLE | 高度坐标 | 990.5 |
| start | INT | 运行状态标志位（0=停止，1=运行） | 0 或 1 |
| xspeed | FLOAT/DOUBLE | X轴速度（**最关键的速度指标**） | 2.5, -1.8, 0.0 |
| yspeed | FLOAT/DOUBLE | Y轴速度 | 0.1, -0.2 |
| updated_at | DATETIME/TIMESTAMP | 数据更新时间戳 | 2026-05-07 14:30:25 |

---

## 二、数据获取方法（完整代码）

### 2.1 基础查询 - 获取所有缆机当前状态

```python
import pymysql
from datetime import datetime

def fetch_all_cable_cars():
    """
    查询所有缆机的最新实时数据
    返回: list[dict] - 包含每台缆机的完整状态信息
    """
    conn = pymysql.connect(
        host='192.168.1.88',
        port=3306,
        user='root',
        password='!Tmhc20170717',
        database='cable_car',
        charset='utf8mb4'
    )

    try:
        cursor = conn.cursor()
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
        cursor.close()

        # 转换为字典列表
        result = []
        for row in rows:
            result.append({
                'car_id': row[0],
                'latitude': float(row[1]) if row[1] else 0.0,
                'longitude': float(row[2]) if row[2] else 0.0,
                'altitude': float(row[3]) if row[3] else 0.0,
                'start': int(row[4]) if row[4] else 0,
                'xspeed': float(row[5]) if row[5] else 0.0,
                'yspeed': float(row[6]) if row[6] else 0.0,
                'updated_at': str(row[7]) if row[7] else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

        return result

    finally:
        conn.close()


# 使用示例
if __name__ == '__main__':
    cable_cars = fetch_all_cable_cars()
    for car in cable_cars:
        print(f"{car['car_id']}号缆机: lat={car['latitude']:.1f}, speed={car['xspeed']:.2f}")
```

### 2.2 定时轮询获取（推荐用于实时监控）

```python
import time
import threading

class CableCarDataFetcher:
    """缆机数据定时获取器"""

    def __init__(self, interval_seconds=3):
        self.interval = interval_seconds
        self._running = False
        self._thread = None
        self._latest_data = {}
        self._callbacks = []

    def on_data_update(self, callback):
        """注册数据更新回调函数"""
        self._callbacks.append(callback)

    def _fetch_and_notify(self):
        """获取数据并通知所有回调"""
        try:
            data = fetch_all_cable_cars()

            # 更新缓存
            for car in data:
                self._latest_data[car['car_id']] = car

            # 通知回调
            for callback in self._callbacks:
                try:
                    callback(data)
                except Exception as e:
                    print(f"回调执行错误: {e}")

        except Exception as e:
            print(f"数据获取失败: {e}")

    def _loop(self):
        """后台循环"""
        while self._running:
            self._fetch_and_notify()
            time.sleep(self.interval)

    def start(self):
        """启动定时获取"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print(f"[Fetcher] 已启动，间隔{self.interval}秒")

    def stop(self):
        """停止获取"""
        self._running = False

    def get_latest(self, car_id=None):
        """获取最新缓存的数锯"""
        if car_id:
            return self._latest_data.get(car_id)
        return self._latest_data


# 使用示例
fetcher = CableCarDataFetcher(interval_seconds=3)

def my_callback(data):
    """处理新数据"""
    for car in data:
        if abs(car['xspeed']) > 0.5:
            print(f"⚡ {car['car_id']}号缆机正在运动 (speed={car['xspeed']:.2f})")

fetcher.on_data_update(my_callback)
fetcher.start()
```

### 2.3 单台缆机查询

```python
def fetch_single_cable_car(car_id):
    """查询单台缆机的最新数据"""
    conn = pymysql.connect(
        host='192.168.1.88',
        port=3306,
        user='root',
        password='!Tmhc20170717',
        database='cable_car',
        charset='utf8mb4'
    )

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cable_car_id, latitude, longitude, altitude,
                   start, xspeed, yspeed, updated_at
            FROM cable_car_status
            WHERE cable_car_id = %s
        """, (car_id,))
        row = cursor.fetchone()
        cursor.close()

        if row:
            return {
                'car_id': row[0],
                'latitude': float(row[1]),
                'longitude': float(row[2]),
                'altitude': float(row[3]),
                'start': int(row[4]),
                'xspeed': float(row[5]),
                'yspeed': float(row[6]),
                'updated_at': str(row[7])
            }
        return None

    finally:
        conn.close()
```

---

## 三、缆机状态判断算法（核心！）

### 3.1 坐标系与位置区域定义

**坐标系说明**:

```
latitude（纬度）坐标轴 - 这是判断缆机位置的核心指标：

数值范围说明：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━→  latitude增大方向
0        40      150     280     450      500+
│         │←─装料区─→│←中途区→│←─卸料区─→│         │
          (loading) (transit) (unloading)

物理意义：
- 低纬度(40-150) → 990装料平台区域
- 中纬度(150-280) → 中途运输区域
- 高纬度(280-450) → 基坑卸料平台区域
```

**位置区域常量定义**:

```python
# ==================== 缆机位置区域定义 ====================
LOADING_ZONE = (40, 150)      # 装料平台区：latitude ∈ [40, 150]
UNLOADING_ZONE = (280, 450)   # 卸料平台区：latitude ∈ [280, 450]
TRANSIT_ZONE = (150, 280)     # 中途区域：latitude ∈ [150, 280]

SPEED_THRESHOLD = 0.5         # 速度判定阈值（单位：米/秒或相应单位）
```

### 3.2 速度字段解读

**xspeed（X轴速度）的含义**:

```
xspeed > 0  →  向高纬度移动（向卸料区方向）= 送料行程
xspeed < 0  →  向低纬度移动（向装料区方向）= 返程行程
xspeed ≈ 0  →  静止或微动

绝对值越大表示运动速度越快
```

**start标志位的含义**:
- `start = 0`: 缆机停止状态（可能正在装卸料）
- `start = 1`: 缆机运行状态（可能在运输中）

⚠️ **注意**: start和xspeed需要结合判断，有时start=1但xspeed≈0表示刚启动或即将停止

### 3.3 状态判断完整算法

```python
def detect_cable_car_state(latitude, xspeed, start):
    """
    检测缆机状态 - 基于位置和速度的综合判断算法

    参数:
        latitude: float - 纬度坐标
        xspeed: float - X轴速度
        start: int - 运行标志(0/1)

    返回:
        tuple: (state, state_label, location)
            - state: 状态代码（英文）
            - state_label: 中文标签
            - location: 位置描述
    """

    # ========== Step 1: 判断当前位置区域 ==========
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

    # ========== Step 2: 根据位置+速度+start综合判断状态 ==========

    # 场景A: 在装料平台区 (latitude 40-150)
    if location_code == "loading_zone":
        if start == 0:
            # start=0 且在装料区 → 正在接料或等待
            return "loading", "990平台接料", location
        else:
            # start=1 在装料区
            if abs(xspeed) < SPEED_THRESHOLD:
                # 速度很慢，仍在接料
                return "loading", "990平台接料", location
            elif xspeed > SPEED_THRESHOLD:
                # 有正向速度，开始离开装料区去送料
                return "delivering", "送料途中", location
            else:
                # 负速度异常情况，仍算接料
                return "loading", "990平台接料", location

    # 场景B: 在卸料平台区 (latitude 280-450)
    if location_code == "unloading_zone":
        if start == 0:
            # start=0 且在卸料区 → 正在卸料
            return "unloading", "基坑卸料", location
        else:
            # start=1 在卸料区
            if abs(xspeed) < SPEED_THRESHOLD:
                # 速度很慢，仍在卸料
                return "unloading", "基坑卸料", location
            elif xspeed < -SPEED_THRESHOLD:
                # 有负向速度，开始离开卸料区返程
                return "returning", "返程途中", location
            else:
                # 正速度异常情况，仍算卸料
                return "unloading", "基坑卸料", location

    # 场景C: 在中途区域 (latitude 150-280)
    if location_code == "transit":
        if xspeed > SPEED_THRESHOLD:
            # 正向速度 → 送料途中
            return "delivering", "送料途中", location
        elif xspeed < -SPEED_THRESHOLD:
            # 负向速度 → 返程途中
            return "returning", "返程途中", location
        else:
            # 速度接近零
            return "delivering" if start == 1 else "stopped", \
                   "送料途中" if start == 1 else "停止", location

    # 场景D: 其他区域（边界情况）
    if location_code == "unknown":
        if xspeed > SPEED_THRESHOLD:
            return "delivering", "送料途中", location
        elif xspeed < -SPEED_THRESHOLD:
            return "returning", "返程途中", location
        else:
            return "stopped", "停止", location

    # 兜底返回
    return "stopped", "停止", location
```

### 3.4 方向检测算法

```python
def detect_cable_car_direction(xspeed, start):
    """
    检测缆机行驶方向

    参数:
        xspeed: float - X轴速度
        start: int - 运行标志

    返回:
        str: 方向标识 ('going'/'returning'/'idle'/'stopped')
    """
    if start == 0:
        return 'stopped'

    if xspeed > 0.5:
        return 'going'       # 去程（送料方向）

    if xspeed < -0.5:
        return 'returning'   # 返程（回装料区方向）

    return 'idle'            # 运行中但速度极低
```

### 3.5 六种状态完整说明表

| 状态码 | 中文标签 | 触发条件 | 物理含义 | 运行强度 |
|--------|----------|----------|----------|----------|
| **loading** | 990平台接料 | 在装料区(40≤lat≤150) + start=0或低速 | 接料/等待 | ⭐ 低（静止）|
| **delivering** | 送料途中 | xspeed>0.5 或 在中途区且start=1 | 向卸料区运送混凝土 | ⭐⭐⭐⭐⭐ 高速运行 |
| **unloading** | 基坑卸料 | 在卸料区(280≤lat≤450) + start=0或低速 | 卸料作业 | ⭐⭐ 中低速 |
| **returning** | 返程途中 | xspeed<-0.5 或 在卸料区且负速度 | 空车返回装料区 | ⭐⭐⭐⭐ 高速运行 |
| **stopped** | 停止 | start=0 且不在特定工作区 | 停机/故障/维护 | ☆ 无 |
| **idle** | 空闲 | start=1 但速度<0.5 | 微动/准备中 | ⭐ 极低 |

---

## 四、数据处理与分析示例（供Agent参考）

### 4.1 实时数据采集与状态标注

```python
class CableCarAnalyzer:
    """缆机数据分析器 - 用于运行强度分析"""

    def __init__(self):
        self.history = {}  # {car_id: [data_points]}
        self.max_history = 1000  # 保留最近1000个数据点

    def analyze_realtime_data(self, raw_data):
        """
        对原始数据进行实时分析和状态标注

        参数:
            raw_data: dict - 来自数据库的原始记录
        返回:
            dict: 增强后的分析结果
        """
        car_id = raw_data['car_id']
        latitude = raw_data['latitude']
        xspeed = raw_data['xspeed']
        start = raw_data['start']

        # 1. 状态检测
        state, state_label, location = detect_cable_car_state(latitude, xspeed, start)

        # 2. 方向检测
        direction = detect_cable_car_direction(xspeed, start)

        # 3. 计算衍生指标
        speed_magnitude = abs(xspeed)  # 速度大小
        is_operating = state in ['delivering', 'returning']  # 是否在运输作业
        is_working = state in ['loading', 'unloading', 'delivering', 'returning']  # 是否在工作周期内

        # 4. 运行强度评估（可根据需要调整算法）
        intensity = self._calculate_intensity(state, xspeed)

        # 5. 构建增强数据
        analyzed = {
            **raw_data,
            'state': state,
            'state_label': state_label,
            'location': location,
            'direction': direction,
            'speed_magnitude': speed_magnitude,
            'is_operating': is_operating,
            'is_working': is_working,
            'intensity': intensity,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # 6. 存入历史
        if car_id not in self.history:
            self.history[car_id] = []
        self.history[car_id].append(analyzed)

        # 7. 保持历史长度
        if len(self.history[car_id]) > self.max_history:
            self.history[car_id] = self.history[car_id][-self.max_history:]

        return analyzed

    def _calculate_intensity(self, state, xspeed):
        """
        计算运行强度指数 (0-100)

        强度标准:
        - loading/unloading: 20-40（低强度作业）
        - delivering/returning: 60-100（高强度运输）
        - stopped/idle: 0-10（停机）
        """
        speed = abs(xspeed)

        if state in ['loading', 'unloading']:
            return min(20 + speed * 10, 40)

        if state in ['delivering', 'returning']:
            return min(60 + speed * 15, 100)

        if state == 'stopped':
            return 0

        return min(speed * 20, 10)  # idle状态

    def get_statistics(self, car_id, time_window_minutes=60):
        """
        获取指定时间窗口内的统计信息

        返回:
            dict: 统计分析结果
        """
        if car_id not in self.history:
            return None

        data_points = self.history[car_id]
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)

        # 过滤时间窗口内的数据
        recent_data = [
            d for d in data_points
            if datetime.strptime(d['timestamp'], '%Y-%m-%d %H:%M:%S') >= cutoff_time
        ]

        if not recent_data:
            return None

        # 计算统计量
        total_points = len(recent_data)
        operating_count = sum(1 for d in recent_data if d['is_operating'])
        working_count = sum(1 for d in recent_data if d['is_working'])

        avg_speed = sum(d['speed_magnitude'] for d in recent_data) / total_points
        max_speed = max(d['speed_magnitude'] for d in recent_data)
        avg_intensity = sum(d['intensity'] for d in recent_data) / total_points

        # 状态分布
        state_distribution = {}
        for d in recent_data:
            s = d['state']
            state_distribution[s] = state_distribution.get(s, 0) + 1

        # 转换为百分比
        state_percentages = {
            k: (v / total_points) * 100
            for k, v in state_distribution.items()
        }

        return {
            'car_id': car_id,
            'time_window_minutes': time_window_minutes,
            'total_data_points': total_points,
            'operating_ratio': (operating_count / total_points) * 100,
            'working_ratio': (working_count / total_points) * 100,
            'avg_speed': round(avg_speed, 3),
            'max_speed': round(max_speed, 3),
            'avg_intensity': round(avg_intensity, 1),
            'state_distribution': state_percentages,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
```

### 4.2 使用示例

```python
# 初始化分析器
analyzer = CableCarAnalyzer()

# 获取原始数据
raw_data = fetch_all_cable_cars()

# 分析每台缆机
for car in raw_data:
    result = analyzer.analyze_realtime_data(car)

    print(f"\n{'='*60}")
    print(f"🚠 {result['car_id']}号缆机 实时分析报告")
    print(f"{'='*60}")
    print(f"📍 位置: {result['location']} (latitude={result['latitude']:.1f})")
    print(f"🔄 状态: {result['state_label']} ({result['state']})")
    print(f"➡️  方向: {result['direction']}")
    print(f"⚡ 速度: xspeed={result['xspeed']:.2f}, |速度|={result['speed_magnitude']:.2f}")
    print(f"💪 运行强度: {result['intensity']}/100")
    print(f"🔧 是否运输中: {'是' if result['is_operating'] else '否'}")
    print(f"📊 是否工作中: {'是' if result['is_working'] else '否'}")

# 获取统计分析（最近1小时）
for car_id in [1, 2, 3, 4]:
    stats = analyzer.get_statistics(car_id, time_window_minutes=60)
    if stats:
        print(f"\n📈 {stats['car_id']}号缆机 最近{stats['time_window_minutes']}分钟统计:")
        print(f"   工作率: {stats['working_ratio']:.1f}%")
        print(f"   运输率: {stats['operating_ratio']:.1f}%")
        print(f"   平均速度: {stats['avg_speed']}")
        print(f"   平均强度: {stats['avg_intensity']}")
        print(f"   状态分布: {stats['state_distribution']}")
```

---

## 五、关键分析维度建议（供Agent开发参考）

### 5.1 运行强度评价指标

建议从以下维度进行缆机运行强度分析：

#### 1️⃣ 时间利用率
```python
# 定义
时间利用率 = (工作时间 / 总时间) × 100%

其中：
- 工作时间 = loading + unloading + delivering + returning 的总时长
- 总时间 = 统计时间段长度
```

#### 2️⃣ 运输效率
```python
# 定义
运输效率 = (运输时间 / 工作时间) × 100%

其中：
- 运输时间 = delivering + returning 的总时长
- 运输时间占比越高，说明缆机在有效运输而非等待
```

#### 3️⃣ 平均运行速度
```python
# 计算
平均速度 = Σ|xspeed| / 数据点数（仅计算operating状态时）

可进一步细分为：
- 送料平均速度（delivering状态的xspeed均值）
- 返程平均速度（returning状态的|xspeed|均值）
```

#### 4️⃣ 循环周期时间
```python
# 一个完整的工作循环：
loading → delivering → unloading → returning → loading

可通过状态转换检测来计算：
- 循环时间 = 两次loading状态之间的时间差
- 平均循环时间 = 多次循环的平均值
- 循环时间稳定性 = 标准差 / 平均值
```

#### 5️⃣ 峰值负载分析
```python
# 检测高强度运行时段
- 当 intensity > 80 时记为高负载
- 统计高负载时段的持续时间
- 识别高频高负载时段（如每天上午10-12点）
```

### 5.2 异常检测建议

```python
# 可检测的异常模式：

1. 长时间停机
   - 条件: 连续N分钟 state='stopped'
   - 可能原因: 设备故障、维护、无任务

2. 速度异常
   - 条件: xspeed超过正常范围（如>10或<-10）
   - 可能原因: 传感器故障、异常操作

3. 区域异常停留
   - 条件: 在中途区域长时间低速
   - 可能原因: 卡顿、障碍物、调度问题

4. 循环时间突变
   - 条件: 本次循环时间 > 平均循环时间 × 1.5倍
   - 可能原因: 装料慢、卸料拥堵、路线问题

5. 频繁启停
   - 条件: 短时间内多次 start 0↔1 切换
   - 可能原因: 操作不稳定、设备问题
```

### 5.3 数据存储建议（如需长期分析）

如果需要进行历史趋势分析，建议将数据持久化：

```sql
-- 创建历史数据表
CREATE TABLE cable_car_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    car_id INT NOT NULL,
    timestamp DATETIME NOT NULL,
    latitude REAL,
    longitude REAL,
    altitude REAL,
    start INT,
    xspeed REAL,
    yspeed REAL,
    state VARCHAR(20),
    state_label VARCHAR(50),
    location VARCHAR(50),
    direction VARCHAR(20),
    intensity FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_car_time (car_id, timestamp),
    INDEX idx_state (state),
    INDEX idx_timestamp (timestamp)
);
```

---

## 六、快速启动模板（复制即用）

### 6.1 最简版数据获取脚本

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缆机实时数据获取脚本 - 最简版本
直接复制运行即可获取数据
"""

import pymysql
import json
from datetime import datetime

# ====== 配置（已填入完整连接信息）======
DB_CONFIG = {
    'host': '192.168.1.88',
    'port': 3306,
    'user': 'root',
    'password': '!Tmhc20170717',
    'database': 'cable_car',
    'charset': 'utf8mb4'
}

def get_cable_car_data():
    """获取所有缆机的当前状态"""
    conn = pymysql.connect(**DB_CONFIG)

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cable_car_id, latitude, longitude, altitude,
                   start, xspeed, yspeed, updated_at
            FROM cable_car_status
            ORDER BY cable_car_id
        """)
        rows = cursor.fetchall()
        cursor.close()

        results = []
        for row in rows:
            results.append({
                'car_id': row[0],
                'lat': float(row[1] or 0),
                'lon': float(row[2 or 0]),
                'alt': float(row[3] or 0),
                'start': int(row[4] or 0),
                'xspeed': float(row[5] or 0),
                'yspeed': float(row[6] or 0),
                'time': str(row[7]) if row[7] else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

        return results

    finally:
        conn.close()


def simple_state_detect(data):
    """简易状态判断（可直接使用）"""
    lat = data['lat']
    xspeed = data['xspeed']
    start = data['start']

    # 位置判断
    if 40 <= lat <= 150:
        zone = "装料区"
        if start == 0 or abs(xspeed) < 0.5:
            state = "loading"
            label = "接料中"
        else:
            state = "delivering"
            label = "开始送料"
    elif 280 <= lat <= 450:
        zone = "卸料区"
        if start == 0 or abs(xspeed) < 0.5:
            state = "unloading"
            label = "卸料中"
        else:
            state = "returning"
            label = "开始返程"
    elif 150 <= lat < 280:
        zone = "中途区"
        if xspeed > 0.5:
            state = "delivering"
            label = "送料中"
        elif xspeed < -0.5:
            state = "returning"
            label = "返程中"
        else:
            state = "idel"
            label = "缓慢移动"
    else:
        zone = "其他"
        state = "unknown"
        label = "未知"

    return {
        **data,
        'zone': zone,
        'state': state,
        'label': label,
        'direction': 'going' if xspeed > 0.5 else ('returning' if xspeed < -0.5 else 'stopped'),
        'intensity': abs(xspeed) * 10  # 简单强度计算
    }


# ====== 主程序 ======
if __name__ == '__main__':
    print("=" * 70)
    print("🚠 缆机实时数据监控系统")
    print(f"⏰ 获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 获取数据
    raw_data = get_cable_car_data()

    # 分析并输出
    for item in raw_data:
        analyzed = simple_state_detect(item)

        print(f"\n{'─'*50}")
        print(f"🚡 {analyzed['car_id']}号缆机")
        print(f"  📍 位置: {analyzed['zone']} (lat={analyzed['lat']:.1f})")
        print(f"  🔄 状态: {analyzed['label']} ({analyzed['state']})")
        print(f"  ➡️  方向: {analyzed['direction']}")
        print(f"  ⚡  速度: xspeed={analyzed['xspeed']:+.2f}")
        print(f"  💪 强度: {analyzed['intensity']:.1f}/100")
        print(f"  🕐 更新: {analyzed['time']}")

    print(f"\n{'='*70}")
    print(f"✅ 共获取 {len(raw_data)} 台缆机数据")
    print("=" * 70)

    # 输出JSON格式（便于系统集成）
    print("\n📦 JSON输出:")
    analyzed_data = [simple_state_detect(d) for d in raw_data]
    print(json.dumps(analyzed_data, ensure_ascii=False, indent=2))
```

### 6.2 定时监控脚本

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缆机定时监控脚本 - 每3秒刷新一次
适合持续运行的监控场景
"""

import time
import pymysql
from datetime import datetime

DB_CONFIG = {
    'host': '192.168.1.88',
    'port': 3306,
    'user': 'root',
    'password': '!Tmhc20170717',
    'database': 'cable_car',
    'charset': 'utf8mb4'
}

INTERVAL = 3  # 监控间隔（秒）

def monitor_loop():
    """持续监控循环"""
    print(f"🚡 缆机监控系统启动")
    print(f"⏱️  刷新间隔: {INTERVAL}秒")
    print(f"💾 数据源: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print("=" * 60)

    while True:
        try:
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cable_car_id, latitude, xspeed, start, updated_at
                FROM cable_car_status
                ORDER BY cable_car_id
            """)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            now = datetime.now().strftime('%H:%M:%S')

            # 清屏效果（可选）
            # print("\033[H\033[J", end="")

            print(f"\n[{now}] 实时状态:")
            print("-" * 60)

            for row in rows:
                car_id, lat, xspeed, start, upd_time = row
                lat = float(lat or 0)
                xspeed = float(xspeed or 0)
                start = int(start or 0)

                # 快速状态判断
                if 40 <= lat <= 150:
                    zone = "装料"
                    state = "接料" if (start == 0 or abs(xspeed) < 0.5) else "出料"
                elif 280 <= lat <= 450:
                    zone = "卸料"
                    state = "卸料" if (start == 0 or abs(xspeed) < 0.5) else "返程"
                else:
                    zone = "中途"
                    state = "运料" if xspeed > 0.5 else ("返程" if xspeed < -0.5 else "待命")

                icon = "🟢" if abs(xspeed) > 0.5 else "🔴"
                print(f"  {icon} {car_id}号 | {zone:<4} | {state:<4} | "
                      f"speed={xspeed:+5.2f} | lat={lat:6.1f}")

            print("-" * 60)
            print(f"按 Ctrl+C 停止监控\n")

            time.sleep(INTERVAL)

        except KeyboardInterrupt:
            print("\n\n👋 监控已停止")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")
            time.sleep(INTERVAL)


if __name__ == '__main__':
    monitor_loop()
```

---

## 七、注意事项与最佳实践

### 7.1 数据库连接管理

⚠️ **重要提醒**:

1. **不要长连接**: 每次查询后务必关闭连接
   ```python
   # ✅ 正确做法
   conn = pymysql.connect(...)
   try:
       # 操作数据库
   finally:
       conn.close()  # 必须关闭！

   # ❌ 错误做法：全局共享一个连接
   global_conn = pymysql.connect(...)  # 会超时断开！
   ```

2. **异常处理**: 务必捕获数据库异常
   ```python
   try:
       data = fetch_data()
   except pymysql.err.OperationalError as e:
       print(f"数据库连接失败: {e}")
       # 重试或降级处理
   except Exception as e:
       print(f"未知错误: {e}")
   ```

3. **超时设置**: 建议添加连接超时
   ```python
   conn = pymysql.connect(
       ...,
       connect_timeout=5,   # 连接超时5秒
       read_timeout=10,     # 读取超时10秒
       write_timeout=10     # 写入超时10秒
   )
   ```

### 7.2 数据质量注意点

1. **空值处理**: 数据库字段可能为NULL
   ```python
   latitude = float(row[1]) if row[1] else 0.0  # 安全转换
   ```

2. **时间同步**: 注意`updated_at`可能与实际时间有延迟
   - 建议同时记录本地接收时间
   - 可用于计算数据新鲜度

3. **数据频率**: 当前系统每3秒同步一次
   - 如果需要更高频率，需要修改数据源端的写入频率
   - 分析时应考虑采样率对精度的影响

### 7.3 性能优化建议

1. **批量查询优于单条查询**
   ```python
   # ✅ 推荐：一次查询所有缆机
   SELECT * FROM cable_car_status ORDER BY cable_car_id

   # ❌ 不推荐：循环查询每台缆机
   for car_id in [1,2,3,4]:
       SELECT * FROM cable_car_status WHERE cable_car_id = car_id
   ```

2. **只查询必要字段**
   ```python
   # 如果只需要位置和速度
   SELECT cable_car_id, latitude, xspeed, start FROM cable_car_status
   ```

3. **考虑使用连接池**（高并发场景）
   ```python
   from dbutils.pooled_db import PooledDB

   pool = PooledDB(
       creator=pymysql,
       maxconnections=5,
       host='192.168.1.88',
       ...
   )

   conn = pool.connection()
   # 使用后自动归还连接池
   ```

---

## 八、扩展接口

### 8.1 如需访问车辆数据

系统还连接了另一个MySQL数据库存储车辆信息：

```python
VEHICLE_DB = {
    'host': '192.168.1.88',
    'port': 3306,
    'user': 'root',
    'password': '!Tmhc20170717',  # 同一密码
    'database': 'vehicle_system',  # 车辆数据库
    'charset': 'utf8mb4'
}

# 核心表: datum_data
# 关键字段: tid, result_x, result_y, speed, lat, lon, time, route
```

如需结合车辆数据进行联合分析（如缆机-车辆协同效率），可以同时查询两个数据库。

---

## 九、总结清单 ✓

在构建缆机运行强度智能分析系统前，请确认以下要点：

- [x] 数据库连接参数已配置（IP/端口/用户名/密码/数据库名）
- [x] 理解cable_car_status表结构（8个关键字段）
- [x] 掌握状态判断算法（基于latitude + xspeed + start）
- [x] 了解六种状态及其物理含义
- [x] 知道坐标系定义（装料区/中途区/卸料区的latitude范围）
- [x] 理解xspeed的正负含义（正=送料，负=返程）
- [x] 能够编写定时数据获取代码（推荐3秒间隔）
- [x] 知道如何进行数据质量处理（空值、异常值）
- [x] 了解可分析的关键指标（利用率、效率、速度、周期时间等）
- [x] 掌握异常检测的基本思路

---

**文档版本**: v1.0 (Agent专用版)
**生成日期**: 2026-05-07
**适用场景**: AI Agent构建缆机运行强度智能分析系统
**密级**: 内部技术文档（含数据库凭据）
