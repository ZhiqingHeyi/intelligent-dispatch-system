# 智能卸料动态匹配调度系统

一个面向缆机协同作业的智能卸料动态匹配调度系统，用于水利枢纽工程中缆机与运输车辆的智能调度匹配。

## 项目简介

本项目是一个基于 Vue 3 + Flask 的智能调度系统，主要功能包括：

- **缆机状态监控**：实时监控缆机的位置、状态、料位等信息
- **车辆调度管理**：管理运输车辆的状态、位置、匹配情况
- **智能匹配算法**：基于 AI 的智能调度算法，实现缆机与车辆的最优匹配
- **AI 智能调度助手**：集成 AI 助手，提供智能调度建议和状态分析

## 技术栈

### 后端
- Python 3.x
- Flask 3.0.0
- PyMySQL 1.1.0
- OpenAI API

### 前端
- Vue 3.4.15
- TypeScript
- Vite 5.0.11
- Pinia 状态管理
- Axios

## 项目结构

```
.
├── dispatch_center/          # Flask 后端
│   ├── app.py               # 主应用入口
│   ├── ai_engine.py         # AI 调度引擎
│   ├── ai_scheduler.py      # AI 调度器
│   ├── database.py          # 数据库操作
│   ├── data_sync.py         # 数据同步
│   ├── static/              # 静态资源
│   └── templates/           # HTML 模板
├── vue-frontend/            # Vue 前端
│   ├── src/
│   │   ├── components/      # 组件
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── api/             # API 接口
│   │   └── types/           # TypeScript 类型定义
│   └── package.json
├── screenshots/             # 项目截图
├── requirements.txt         # Python 依赖
└── README.md
```

## 功能截图

### 调度中心主界面
![调度中心主界面](screenshots/screenshot1.png)

### AI 智能调度助手
![AI 智能调度助手](screenshots/screenshot2.png)

## 安装与运行

### 后端部署

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 配置数据库
修改 `config.py` 中的数据库连接信息

3. 启动服务
```bash
python dispatch_center/app.py
```

### 前端开发

1. 进入前端目录
```bash
cd vue-frontend
```

2. 安装依赖
```bash
npm install
```

3. 启动开发服务器
```bash
npm run dev
```

4. 构建生产版本
```bash
npm run build
```

## 许可证

MIT License
