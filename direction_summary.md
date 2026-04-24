# 缆机返程与车辆送料方向判断特征总结

## 一、缆机返程特征（cable_car 数据库）

### 1.1 数据库表
- **实时状态表**: `cable_car_status` - 存储当前位置和速度
- **历史轨迹表**: `cable_car_positions` - 存储历史轨迹数据

### 1.2 坐标系说明
| 位置 | latitude (X) | 说明 |
|------|-------------|------|
| 装料平台 | ~79-132 | 低纬度区域 |
| 卸料平台 | ~339 | 高纬度区域 |

### 1.3 返程判断逻辑
**核心原则**: 送料时 X速度 > 0，返程时 X速度 < 0

| 方向 | X速度 (xspeed) | 纬度变化 | 说明 |
|------|---------------|---------|------|
| **往程** (装料→卸料) | xs > 0 | 纬度增加 | 向卸料点移动 |
| **返程** (卸料→装料) | xs < 0 | 纬度减小 | 向装料点移动 |

### 1.4 SQL判断语句
```sql
-- 判断缆机方向
SELECT 
    cable_car_id,
    latitude,
    xspeed,
    yspeed,
    CASE 
        WHEN xspeed > 0.5 THEN '往程（送料）'
        WHEN xspeed < -0.5 THEN '返程（往回走）'
        ELSE '停止/调整'
    END as direction
FROM cable_car_status;
```

---

## 二、车辆送料方向特征（vehicle_system 数据库）

### 2.1 数据库表
- **车辆数据表**: `datum_data` - 存储车辆实时位置和状态

### 2.2 坐标系说明（基于Y字形分叉路）
| 位置 | result_y (Y坐标) | 说明 |
|------|-----------------|------|
| 右端（起点/接料点） | ~87（原-338区域） | Y值较大 |
| 左端（终点/卸料点） | ~-1200 | Y值较小 |

**注意**: 实际数据显示Y坐标范围从 -1387 到 87，正值在右端起点区域。

### 2.3 送料方向判断逻辑
**核心原则**: 主要依靠 **result_y** 的变化判断方向

| 方向 | Y坐标变化 | 说明 |
|------|----------|------|
| **往程** (右→左) | Y值逐渐**减小** (87 → -1000) | 从起点向终点 |
| **返程** (左→右) | Y值逐渐**增大** (-1000 → 87) | 从终点返回起点 |

### 2.4 关键阈值
- **变化阈值**: |ΔY| > 10 认为有方向变化（过滤信号跳跃）
- **位置分区**:
  - Y > -400: 右端起点区
  - -600 < Y <= -400: 右中段
  - -800 < Y <= -600: 左中段
  - Y <= -800: 左端终点区

### 2.5 SQL判断语句
```sql
-- 方法1: 判断车辆方向（基于Y变化）
SELECT 
    tid,
    user_name,
    result_y,
    time,
    LAG(result_y) OVER (PARTITION BY tid ORDER BY time) as prev_y,
    result_y - LAG(result_y) OVER (PARTITION BY tid ORDER BY time) as delta_y,
    CASE 
        WHEN result_y - LAG(result_y) OVER (...) < -10 
        THEN '往程(右→左)'
        WHEN result_y - LAG(result_y) OVER (...) > 10 
        THEN '返程(左→右)'
        ELSE '静止/跳跃'
    END as direction
FROM datum_data;

-- 方法2: 判断当前区域
SELECT 
    tid,
    user_name,
    result_y,
    CASE 
        WHEN result_y > -400 THEN '右端起点区'
        WHEN result_y BETWEEN -800 AND -400 THEN '中途区'
        WHEN result_y <= -800 THEN '左端终点区'
    END as y_zone
FROM datum_data;
```

---

## 三、两种系统对比总结

| 特征 | 缆机系统 | 车辆系统 |
|------|---------|---------|
| **主坐标** | latitude (X) | result_y (Y) |
| **方向判断** | X速度正负 | Y值变化趋势 |
| **往程特征** | xspeed > 0 | Y值减小 |
| **返程特征** | xspeed < 0 | Y值增大 |
| **起点位置** | latitude ~79-132 | result_y ~87 |
| **终点位置** | latitude ~339 | result_y ~-1200 |
| **数据表** | cable_car_status | datum_data |

### 3.1 共同特点
1. 都使用 **坐标变化** 来判断行驶方向
2. 都需要设置 **阈值** 过滤信号噪声/跳跃
3. 都可以通过 **连续轨迹点** 的对比来判断趋势

### 3.2 差异点
1. **缆机**: 主要靠 **速度方向** (xspeed正负) 判断
2. **车辆**: 主要靠 **位置变化** (Y值增减) 判断
3. **缆机**: 坐标是 **纬度** 概念，范围较小
4. **车辆**: 坐标是 **相对位置**，范围较大且可能有跳跃

---

## 四、实际应用建议

### 4.1 缆机返程检测
```python
# 判断缆机是否返程
def is_cable_car_returning(xspeed):
    return xspeed < -0.5  # X速度为负且绝对值大于阈值
```

### 4.2 车辆往程检测
```python
# 判断车辆是否从右端向左端（往程）
def is_vehicle_going(prev_y, curr_y, threshold=10):
    delta = curr_y - prev_y
    return delta < -threshold  # Y值明显减小
```

### 4.3 数据库联合查询
如果需要同时监控两种设备，可以分别查询后统一处理：

```sql
-- 缆机状态查询
SELECT 'cable_car' as type, cable_car_id as id, xspeed, 
       CASE WHEN xspeed < 0 THEN 'returning' ELSE 'going' END as status
FROM cable_car.cable_car_status;

-- 车辆状态查询  
SELECT 'vehicle' as type, tid as id, result_y,
       LAG(result_y) OVER (PARTITION BY tid ORDER BY time) as prev_y
FROM vehicle_system.datum_data;
```

---

## 五、总结

**缆机返程特征**: 
- 核心看 **xspeed < 0**（负值）
- 从卸料区（latitude高）返回装料区（latitude低）

**车辆送料特征**:
- 核心看 **result_y 减小**（从正值到负值）
- 从右端起点（Y≈87）向左端终点（Y≈-1000）
- 需要处理信号跳跃（设置|ΔY|>10阈值）
