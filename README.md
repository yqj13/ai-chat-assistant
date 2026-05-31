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

- Node.js >= 20.19.0 或 >= 22.12.0
- Python 3.11+

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
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
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

## 核心功能实现

### 1. 深度思考 (Deep Thinking)

**方案设计**:
- 通过 OpenAI SDK 直接调用支持 thinking 模式的模型
- 在请求中设置 `extra_body={"thinking": {"type": "enabled"}}`
- 流式接收 `reasoning_content` 并实时展示
- 思考过程可折叠/展开

**核心代码**:

后端 ([`backend/chat_service.py`](file:///d:/ai_chat/backend/chat_service.py#L300-L403)):
```python
async def _execute_deep_thinking_stream(self, messages, uid, message_id, history_key, context_id):
    client = AsyncOpenAI(base_url=settings.API_URL, api_key=settings.API_KEY)
    stream = await client.chat.completions.create(
        model=settings.MODEL_NAME,
        messages=messages,
        extra_body={"thinking": {"type": "enabled"}},
        stream=True
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta
        if hasattr(delta, "reasoning_content") and delta.reasoning_content:
            current_reasoning_content += delta.reasoning_content
            stream_chunk = StreamChunk(
                reasoning_content=delta.reasoning_content,
                message_id=message_id,
                type=MessageType.TEXT
            )
            await sse_manager.send_message(uid, message_id, json.dumps(stream_chunk.dict()))
```

前端 ([`frontend/src/components/ChatMessages.vue`](file:///d:/ai_chat/frontend/src/components/ChatMessages.vue#L14-L16)):
```vue
<t-chat-thinking 
    :content="{ title: msg.thinking ? '思考中' : '思考完成', text: msg.reasoningContent }"
    :collapsed="msg.collapsed || false"
    :status="msg.thinking ? 'pending' : 'complete'"
/>
```

### 2. 联网查询 (Web Search)

**方案设计**:
- 集成博查 AI 搜索 API
- 支持用户强制触发搜索（`web_search=true`）
- 搜索结果以列表形式展示，包含标题、链接、摘要和站点名称
- 支持点击链接跳转到原始网页

**核心代码**:

工具定义 ([`backend/tools.py`](file:///d:/ai_chat/backend/tools.py#L115-L190)):
```python
@tool("web_search", args_schema=SearchInput)
def search_web(query: str, num_results: int = 3) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.BOCHA_API_KEY}"
    }
    data = {"query": query, "freshness": "noLimit", "summary": True, "count": num_results}
    response = requests.post(settings.BOCHA_API_URL, headers=headers, json=data)
    # 解析并格式化搜索结果
    return formatted_results
```

前端展示 ([`frontend/src/components/ChatMessages.vue`](file:///d:/ai_chat/frontend/src/components/ChatMessages.vue#L76-L85)):
```vue
<div v-else-if="part.result.tool === 'web_search'" class="result-table">
    <div v-for="(item, idx) in getSearchTableData({ data: part.result })" :key="idx" class="search-result-item">
        <div class="search-result-title">
            <a :href="item.url" target="_blank" class="search-link">{{ item.title }}</a>
            <span v-if="item.siteName" class="site-name">{{ item.siteName }}</span>
            <span v-if="item.date" class="search-date">{{ item.date }}</span>
        </div>
        <div v-if="item.snippet" class="search-result-snippet">{{ item.snippet }}</div>
    </div>
</div>
```

### 3. 工具调用 (Tool Calling)

**方案设计**:
- 使用 LangChain 构建 Agent
- 支持天气查询、计算器、时间查询、网络搜索等工具
- 通过 `astream_events` 实时捕获工具调用事件
- 前端可折叠展示工具参数和执行结果

**核心代码**:

工具创建 ([`backend/tools.py`](file:///d:/ai_chat/backend/tools.py#L237-L238)):
```python
def create_tools():
    return [get_weather, search_web, calculate, get_current_time]
```

Agent 执行 ([`backend/chat_service.py`](file:///d:/ai_chat/backend/chat_service.py#L431-L609)):
```python
async def _execute_agent_stream(self, messages, uid, message_id, history_key, web_search, context_id):
    agent = self._create_agent(deep_thinking=False)
    async for event in agent.astream_events(
        {"messages": langchain_messages},
        config=config,
        version="v2"
    ):
        if kind == "on_tool_start":
            tool_name = event["name"]
            tool_inputs = event["data"].get("input", {})
            # 发送工具开始事件
        elif kind == "on_tool_end":
            tool_output = event["data"].get("output", "")
            # 发送工具结束和结果事件
```

### 4. 短期记忆 (Short-term Memory)

**方案设计**:
- 使用 `SSEManager` 管理流式消息的内存缓存
- 支持断点续传，通过 `sequence` 编号和 `message_id` 追踪消息状态
- 连接断开后可从缓存中重放未完成的消息
- 内存缓存会在用户清理或超时后释放

**核心代码**:

SSE 管理 ([`backend/sse_manager.py`](file:///d:/ai_chat/backend/sse_manager.py#L10-L179)):
```python
class SSEManager:
    def __init__(self):
        self.message_cache: Dict[str, Dict[str, list]] = defaultdict(dict)
        self.message_sequences: Dict[str, Dict[str, int]] = defaultdict(dict)
    
    async def send_message(self, uid: str, message_id: str, content: str):
        # 存储消息并分配 sequence 编号
        self.message_cache[uid][message_id].append(content)
        self.message_sequences[uid][message_id] += 1
    
    async def get_cached_messages(self, uid: str, message_id: str, from_sequence: int = 0):
        # 获取指定 message_id 的缓存消息用于断点续传
        return messages[from_sequence - 1:]
```

前端状态管理 ([`frontend/src/utils/index.js`](file:///d:/ai_chat/frontend/src/utils/index.js)):
```javascript
class ChatStateManager {
    setStreamState(messageId, sequence) {
        localStorage.setItem(`chat_state_${this.uid}`, JSON.stringify({ messageId, sequence }));
    }
    getStreamState() {
        const saved = localStorage.getItem(`chat_state_${this.uid}`);
        return saved ? JSON.parse(saved) : null;
    }
}
```

### 5. 对话管理 (Conversation Management)

**方案设计**:
- 使用 MySQL 数据库持久化用户、会话和消息数据
- 支持多会话管理，用户可创建、切换、删除会话
- 会话列表按时间排序，自动生成会话标题
- 历史对话从数据库加载到内存中供 Agent 使用

**核心代码**:

数据库模型 ([`backend/database.py`](file:///d:/ai_chat/backend/database.py#L10-L60)):
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True)
    sessions = relationship("Session", back_populates="user")

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), unique=True)
    messages = relationship("Message", back_populates="session")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    message_id = Column(String(255), unique=True)
    session_id = Column(String(255), ForeignKey("sessions.session_id"))
    role = Column(String(50))
    content = Column(Text)
    reasoning_content = Column(Text)
```

前端会话管理 ([`frontend/src/composables/useConversation.js`](file:///d:/ai_chat/frontend/src/composables/useConversation.js#L45-L104)):
```javascript
const createNewConversation = async () => {
    const session = await userApi.createSession(uid.value, null, '新对话');
    conversations.value.unshift({
        id: session.session_id,
        title: session.title || '新对话',
        timestamp: Date.now()
    });
    currentConversation.value = conversations.value[0];
};

const selectConversation = async (conv) => {
    currentConversation.value = conv;
    await loadConversationMessages(conv);
};
```

