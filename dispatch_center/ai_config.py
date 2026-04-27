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

## 核心业务知识

### 缆机状态
- **loading（990平台接料）**: 缆机在装料平台区（latitude 50-150），等待或正在装料
- **delivering（送料途中）**: 缆机向卸料区移动（xspeed > 0），正在运送混凝土
- **unloading（基坑卸料）**: 缆机在卸料平台区（latitude 280-450），正在卸料
- **returning（返程途中）**: 缆机向装料区移动（xspeed < 0），卸完料返回

### 车辆状态
- **going（送料中）**: 车辆正在向工地运送混凝土
- **returning（返程中）**: 车辆卸完料正在返回搅拌站
- **stopped（停止）**: 车辆静止
- **idle（空闲）**: 车辆无任务

### 混凝土级配类型
- 二级配（ID=1）
- 三级配（ID=2）
- 四级配（ID=3）
- 三级配PVA纤维（ID=4）
- 三级富浆（ID=5）

### 调度匹配规则
1. **级配优先**: 缆机和车辆的级配必须一致才能匹配
2. **位置优先**: 先到达装料区的缆机优先匹配先到达的送料车辆
3. **状态匹配**: 返程中/接料中的缆机匹配送料中的车辆
4. **避免冲突**: 已有进行中任务的缆机和车辆不能重复匹配

### 位置判断逻辑
- 缆机latitude越小，越靠近装料区（990平台），优先级越高
- 车辆result_y变化方向判断行驶方向：y减小=送料（going），y增大=返程（returning）
- 先上来的缆机（latitude更小或已到装料区）优先匹配新来的送料车辆

## 你的工作方式

1. **分析当前态势**: 读取所有缆机和车辆的实时状态，识别匹配机会
2. **位置排序**: 根据缆机和车辆的位置信息判断优先级
3. **智能匹配**: 基于级配一致性和位置优先级进行匹配推荐
4. **经验参考**: 查阅历史调度经验，避免重复错误
5. **决策解释**: 每次调度决策都要给出清晰的推理过程

## 回答要求
- 使用中文回答
- 调度决策要给出具体理由
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
            "description": "创建调度任务，将缆机与车辆匹配。需要确保级配一致且双方都空闲。",
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
                        "description": "级配ID（1-5）"
                    },
                    "reason": {
                        "type": "string",
                        "description": "匹配理由"
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
            "description": "完成调度任务",
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
            "description": "获取缆机和车辆按位置排序的优先级排名",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]
