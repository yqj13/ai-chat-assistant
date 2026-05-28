# AI Chat 前后端联调测试指南

## 前置条件

### 1. 确保后端服务正在运行
后端服务应该运行在 `http://localhost:8000`

启动后端：
```bash
cd backend
python main.py
```

### 2. 安装前端依赖
```bash
cd frontend
npm install
```

## 启动前端服务

```bash
cd frontend
npm run dev
```

前端服务通常运行在 `http://localhost:5173`

## 测试步骤

### 1. 访问前端页面
在浏览器中打开 `http://localhost:5173`

### 2. 检查连接状态
页面右上角应该显示 "Online" 状态，表示成功连接到后端服务。

### 3. 测试功能

#### 测试时间查询
输入：`现在几点了？`
预期：返回当前时间信息

#### 测试计算器
输入：`计算 2+3*4`
预期：返回计算结果 14

#### 测试天气查询
输入：`北京的天气怎么样？`
预期：返回北京天气信息（如果工具可用）

#### 测试联网搜索
输入：`搜索 Python`
预期：返回搜索结果（如果工具可用）

#### 测试普通对话
输入：`你好`
预期：返回AI的友好回复

## 故障排查

### 问题1：显示 "Offline"
- 检查后端服务是否启动
- 检查后端服务端口是否为 8000
- 检查浏览器控制台是否有错误信息

### 问题2：消息发送后无响应
- 检查后端服务是否正常运行
- 检查浏览器控制台的 Network 标签页
- 查看后端终端的日志输出

### 问题3：SSE 连接失败
- 确保后端支持 CORS
- 检查浏览器是否阻止了 SSE 连接
- 查看浏览器控制台的错误信息

## API 接口说明

### POST /api/chat
发送聊天消息

请求体：
```json
{
  "content": "消息内容",
  "uid": "用户ID",
  "context_id": "上下文ID",
  "last_message_id": "上一条消息ID（可选）"
}
```

响应：
```json
{
  "status": "success",
  "message_id": "消息ID"
}
```

### GET /api/stream/{uid}/{message_id}
SSE 流式响应接口

返回格式：
```
data: {"status": false, "content": "内容片段", "message_id": "xxx"}

data: {"status": true, "content": "", "message_id": "xxx", "finish_reason": "stop"}
```

## 技术栈

- **前端**：Vue 3 + Vite + Axios
- **后端**：FastAPI + LangChain + LangGraph
- **通信**：REST API + SSE (Server-Sent Events)
