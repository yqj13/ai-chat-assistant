
# AI Chat 项目

一个现代化的 AI 聊天应用，采用前后端分离架构。

## 技术栈

### 前端
- **框架**: Vue 3 (beta)
- **构建工具**: Vite 8
- **状态管理**: Pinia 3
- **路由**: Vue Router 5
- **HTTP 客户端**: Axios 1
- **测试**: Vitest
- **代码规范**: ESLint + Prettier + Oxlint

### 后端
- **Web 框架**: FastAPI 0.109
- **ASGI 服务器**: Uvicorn 0.27
- **数据验证**: Pydantic 2.6
- **HTTP 请求**: Requests 2.31

## 项目结构

```
ai_chat/
├── backend/              # 后端服务
│   ├── main.py          # FastAPI 主应用
│   ├── requirements.txt # Python 依赖
│   └── .env.example     # 环境变量示例
└── frontend/            # 前端应用
    ├── src/
    │   ├── components/  # 组件目录
    │   ├── views/       # 页面视图
    │   ├── router/      # 路由配置
    │   ├── stores/      # Pinia 状态管理
    │   └── main.js      # 应用入口
    ├── package.json
    └── vite.config.js
```

## 运行指南

### 前置要求

- Node.js &gt;= 20.19.0 或 &gt;= 22.12.0
- Python 3.8+

### 后端启动

1. 进入后端目录：
   ```bash
   cd backend
   ```

2. 创建虚拟环境（可选但推荐）：
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

4. 启动服务：
   ```bash
   python main.py
   ```

   后端服务将在 `http://localhost:8000` 启动

### 前端启动

1. 进入前端目录：
   ```bash
   cd frontend
   ```

2. 安装依赖：
   ```bash
   npm install
   ```

3. 启动开发服务器：
   ```bash
   npm run dev
   ```

   前端服务将在 `http://localhost:5173` 启动

### 其他命令

**前端命令：**
```bash
npm run build        # 构建生产版本
npm run preview      # 预览生产构建
npm run test:unit    # 运行单元测试
npm run lint         # 代码检查
npm run format       # 代码格式化
```

**后端 API 文档：**
启动后端服务后，访问 `http://localhost:8000/docs` 查看自动生成的 API 文档。

## 功能点

### 已实现功能
- 前后端分离架构
- RESTful API 接口
- 消息传递模型
- CORS 跨域支持
- 健康检查端点

### 核心特性
- 实时聊天界面
- 可扩展的 AI 模型支持
- 消息历史记录
- 响应式设计

## 核心方案设计

### 架构设计
采用典型的前后端分离架构：
- 前端负责用户界面展示和交互
- 后端提供 RESTful API 服务
- 通过 HTTP 协议进行通信

### API 设计
- `GET /` - 服务状态检查
- `GET /health` - 健康检查
- `POST /api/chat` - 聊天接口

### 数据模型
- **Message**: 包含角色和内容的消息对象
- **ChatRequest**: 聊天请求，包含消息列表和模型选择
- **ChatResponse**: 聊天响应，包含 AI 回复

### 前端设计
- 使用 Vue 3 Composition API
- Pinia 进行状态管理
- Vue Router 管理路由
- 组件化开发模式
