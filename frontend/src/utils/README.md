# 工具函数模块

本目录包含项目中可复用的工具函数。

## 目录结构

```
utils/
├── index.js          # 统一导出
├── formatTime.js     # 时间格式化工具
├── storage.js        # 存储管理工具
└── message.js        # 消息处理工具
```

## 使用方法

### 时间格式化

```javascript
import { formatTime, formatTimeShort, formatDateTime } from '../utils'

// 完整时间格式：刚刚、x分钟前、今天 xx:xx、昨天 xx:xx、MM/DD HH:MM
formatTime(timestamp)

// 短时间格式：刚刚、x分钟前、x小时前、x天前、MM/DD
formatTimeShort(timestamp)

// 完整日期时间：YYYY-MM-DD HH:mm:ss
formatDateTime(timestamp)
```

### 存储管理

```javascript
import { storage, ChatStateManager } from '../utils'

// 直接使用 storage
storage.get('key', defaultValue)
storage.set('key', value)
storage.remove('key')

// 使用 ChatStateManager 管理聊天状态
const manager = new ChatStateManager(uid)
manager.getStreamState()          // 获取流状态
manager.setStreamState(msgId, seq) // 设置流状态
manager.getConversationId()       // 获取会话ID
manager.setConversationId(id)    // 设置会话ID
manager.clearAll()               // 清除所有状态
```

### 消息处理

```javascript
import { 
  mapServerMessagesToLocal,
  createUserMessage,
  createAssistantMessage,
  createTextPart,
  createToolCallPart,
  extractTextFromMessage
} from '../utils'

// 将服务器消息映射为本地格式
mapServerMessagesToLocal(serverMessages)

// 创建消息对象
createUserMessage('Hello', { deepThinking: true, webSearch: false })
createAssistantMessage('msg_123')

// 创建消息片段
createTextPart('内容')
createToolCallPart({ tool: 'weather', params: {} }, { result: '晴' })

// 从消息中提取文本
extractTextFromMessage(message)
```

## 最佳实践

1. **统一导入**：从 `../utils` 统一导入所有工具函数
2. **错误处理**：工具函数内部已经处理了常见错误，无需额外 try-catch
3. **类型安全**：使用 TypeScript 时建议添加类型定义
4. **单元测试**：建议为复杂工具函数编写单元测试
