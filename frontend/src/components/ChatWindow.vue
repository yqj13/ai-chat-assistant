<template>
  <div class="chat-window">
    <div class="chat-header">
      <h2>AI Chat Assistant</h2>
      <span class="status" :class="{ online: isOnline }">
        {{ isOnline ? 'Online' : 'Offline' }}
      </span>
    </div>
    
    <div ref="messagesContainer" class="messages-container">
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon">🤖</div>
        <p>欢迎使用AI聊天助手</p>
        <p class="hint">支持：天气查询、计算器、时间查询、联网搜索</p>
      </div>
      <ChatMessage
        v-for="(message, index) in messages"
        :key="index"
        :message="message"
      />
    </div>
    
    <ChatInput :is-loading="isLoading" @send="handleSend" />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, onUnmounted } from 'vue'
import ChatMessage from './ChatMessage.vue'
import ChatInput from './ChatInput.vue'
import axios from 'axios'

const messages = ref([])
const isLoading = ref(false)
const isOnline = ref(false)
const messagesContainer = ref(null)
const eventSource = ref(null)

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

watch(messages, scrollToBottom, { deep: true })

const checkOnlineStatus = async () => {
  try {
    await axios.get('http://localhost:8000/health')
    isOnline.value = true
  } catch {
    isOnline.value = false
  }
}

const closeEventSource = () => {
  if (eventSource.value) {
    eventSource.value.close()
    eventSource.value = null
  }
}

const handleSend = async (text) => {
  messages.value.push({ role: 'user', content: text })
  
  messages.value.push({
    role: 'assistant',
    content: '',
    thinking: '正在分析问题...',
    finished: false,
    messageId: null
  })
  
  isLoading.value = true
  
  try {
    const response = await axios.post('http://localhost:8000/v1/chat/completions', {
      model: 'gpt-3.5-turbo',
      messages: [{ role: 'user', content: text }],
      tools: [
        {
          type: "function",
          function: {
            name: "get_weather",
            description: "获取指定城市的当前天气信息",
            parameters: {
              type: "object",
              properties: {
                city: { type: "string", description: "城市名称" }
              },
              required: ["city"]
            }
          }
        },
        {
          type: "function",
          function: {
            name: "web_search",
            description: "联网搜索相关信息",
            parameters: {
              type: "object",
              properties: {
                query: { type: "string", description: "搜索关键词" }
              },
              required: ["query"]
            }
          }
        },
        {
          type: "function",
          function: {
            name: "calculator",
            description: "执行数学计算",
            parameters: {
              type: "object",
              properties: {
                expression: { type: "string", description: "数学表达式" }
              },
              required: ["expression"]
            }
          }
        },
        {
          type: "function",
          function: {
            name: "get_current_time",
            description: "获取当前时间",
            parameters: { type: "object", properties: {} }
          }
        }
      ],
      tool_choice: "auto",
      temperature: 0.3
    })
    
    const botIndex = messages.value.length - 1
    const reply = response.data.choices[0].message.content
    
    messages.value[botIndex].content = reply
    messages.value[botIndex].finished = true
    messages.value[botIndex].thinking = ''
    
    if (response.data.choices[0].finish_reason === 'tool_calls') {
      messages.value[botIndex].toolUsed = response.data.choices[0].message.tool_calls?.[0]?.function.name
    }
    
  } catch (error) {
    console.error('API调用失败:', error)
    const botIndex = messages.value.length - 1
    messages.value[botIndex].content = '抱歉，服务器暂时无法响应，请稍后重试。'
    messages.value[botIndex].finished = true
    messages.value[botIndex].thinking = ''
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  checkOnlineStatus()
  setInterval(checkOnlineStatus, 5000)
})

onUnmounted(() => {
  closeEventSource()
})
</script>

<style scoped>
.chat-window {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f8f9fa;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chat-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.status {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.2);
}

.status.online {
  background: rgba(56, 239, 125, 0.3);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #6b7280;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-state p {
  margin: 8px 0;
  font-size: 16px;
}

.empty-state .hint {
  font-size: 14px;
  color: #9ca3af;
}
</style>