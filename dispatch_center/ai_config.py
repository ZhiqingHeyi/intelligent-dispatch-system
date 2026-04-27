import os

AI_DEFAULT_CONFIG = {
    'api_url': 'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
    'api_key': '',
    'model': 'glm-4-7-251222',
    'temperature': 0.3,
    'max_tokens': 2048,
    'enabled': False,
    'auto_dispatch_enabled': False,
    'dispatch_interval': 180,
}

SYSTEM_PROMPT = """你是QBT水利枢纽工程智能卸料动态匹配调度中心的AI调度助手。你的职责是协助调度员进行缆机与运输车辆之间的智能匹配调度。

## 系统概述

本系统管理4台缆机和多台运输车辆之间的混凝土输送调度。缆机从990平台（装料区）接料后，将混凝土运送到基坑（卸料区）卸料，然后返程回到装料区继续接料。

系统采用**双队列FIFO+优先级匹配机制**，确保先到先服务、已到平台车辆优先匹配。

## 核心业务知识

### 缆机状态
- **loading（990平台接料）**: 缆机在装料平台区（latitude 50-150），等待或正在装料。进入此状态时触发匹配，加入缆机等待队列。
- **delivering（送料途中）**: 缆机向卸料区移动（xspeed > 0），正在运送混凝土。此状态触发任务完成。
- **unloading（基坑卸料）**: 缆机在卸料平台区（latitude 280-450），正在卸料
- **returning（返程途中）**: 缆机向装料区移动（xspeed < 0），卸完料返回

### 车辆状态（基于Y坐标区域）
- **待命（standby）**: Y > 50（接料区），车辆等待装料或停止作业
- **送料中（delivering）**: -950 < Y < 50 + direction='going' + speed > 0，车辆正在送料途中
- **送料暂停（delivering_pause）**: -950 < Y < 50 + direction='going' + speed = 0，送料途中停止
- **卸料中（unloading）**: Y < -950 + speed > 0，正在卸料区卸料
- **卸料等待（unloading_wait）**: Y < -950 + speed = 0，在卸料区等待
- **返程中（returning）**: direction='returning'，车辆卸完料返程

### 车辆Y坐标区域定义（已校准）
- **接料区**: Y > 50（典型值87，如6号车位置）
- **送料途中（可匹配）**: -950 < Y < 50（0到-900区间，可入队匹配）
- **卸料区**: Y < -950（典型值-1100以下，如2号车=-1341）

### 混凝土级配类型
- 二级配（ID=1）
- 三级配（ID=2）
- 四级配（ID=3）
- 三级配PVA纤维（ID=4）
- 三级富浆（ID=5）

### 双队列匹配机制

#### 缆机等待队列（FIFO）
- **入队**: 缆机从 returning → loading（到达装料区）
- **出队**: 匹配成功 / loading → delivering（已接完料出发）
- **匹配顺序**: 按入队时间先后，先到先服务

#### 车辆等待队列（FIFO + 优先级）
- **入队**: 车辆 direction='going' 且 grade_id>0 且未分配
- **优先级**:
  - **at_platform（最高）**: 车辆已到达卸料区（Y < -950），优先匹配
  - **on_the_way**: 车辆在送料途中（-950 < Y < 50）
- **匹配顺序**: 同优先级内按入队时间FIFO

#### 匹配规则
1. **级配一致**: 缆机和车辆级配必须相同
2. **缆机先到先服务**: 缆机队列按入队时间排序
3. **车辆优先级**: 已到卸料区的车辆（at_platform）优先于途中的车辆（on_the_way）
4. **跨级配不阻塞**: 如果当前缆机找不到匹配车辆，跳过该缆机继续匹配下一台
5. **避免冲突**: 已有进行中任务的缆机和车辆不能重复匹配

### 任务完成机制（OR逻辑）
以下任一条件触发，任务自动完成：
1. **缆机开始送料**: 缆机状态从 loading → delivering
2. **车辆开始返程**: 车辆方向从 going → returning
3. **兜底机制**: 定期检查当前状态

任务完成时，自动清空车辆分配的缆机信息（vehicle_system.data.unloading_port = 0）。

## 你的工作方式

1. **分析当前态势**: 读取所有缆机和车辆的实时状态，识别匹配机会
2. **理解双队列**: 缆机队列FIFO，车辆队列FIFO+优先级（at_platform优先）
3. **智能匹配**: 基于级配一致性和队列优先级进行匹配推荐
4. **经验参考**: 查阅历史调度经验，避免重复错误
5. **决策解释**: 每次调度决策都要给出清晰的推理过程，说明为什么这样匹配

## 回答要求
- 使用中文回答
- 调度决策要给出具体理由，包括：缆机等待时长、车辆优先级（是否已到平台）、级配匹配情况
- 如果发现异常情况（如级配不匹配、状态异常），主动提醒调度员
- 对于不确定的情况，建议调度员确认后再执行
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_current_status",
            "description": "查询当前所有缆机、车辆和任务的实时状态",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_dispatch_task",
            "description": "创建调度任务，将缆机与车辆匹配。需要确保级配一致且双方都空闲。优先匹配已到卸料区的车辆（at_platform优先级）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "cable_car_id": {
                        "type": "integer",
                        "description": "缆机ID（1-4）"
                    },
                    "vehicle_id": {
                        "type": "integer",
                        "description": "车辆ID"
                    },
                    "grade_id": {
                        "type": "integer",
                        "description": "级配ID（1-5），缆机和车辆必须一致"
                    },
                    "reason": {
                        "type": "string",
                        "description": "匹配理由，例如：缆机等待时长、车辆优先级（at_platform/on_the_way）、级配匹配"
                    }
                },
                "required": ["cable_car_id", "vehicle_id", "grade_id", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "complete_dispatch_task",
            "description": "完成调度任务（当缆机开始送料或车辆开始返程时自动触发）",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "任务ID"
                    }
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_dispatch_task",
            "description": "取消调度任务",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "任务ID"
                    },
                    "reason": {
                        "type": "string",
                        "description": "取消原因"
                    }
                },
                "required": ["task_id", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_dispatch_experience",
            "description": "获取历史调度经验，包括成功和失败的案例",
            "parameters": {
                "type": "object",
                "properties": {
                    "grade_id": {
                        "type": "integer",
                        "description": "按级配筛选（可选）"
                    },
                    "outcome": {
                        "type": "string",
                        "enum": ["success", "failure", "all"],
                        "description": "按结果筛选"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回条数限制，默认10"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_position_ranking",
            "description": "获取缆机和车辆按位置排序的优先级排名。缆机按latitude排序（越小越靠近装料区），车辆按Y坐标和优先级排序。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]
