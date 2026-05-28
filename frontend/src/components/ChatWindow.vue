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

const API_BASE_URL = 'http://localhost:8000'
const USER_ID = `user_${Date.now()}`

const MESSAGE_TYPES = {
  TEXT: 0,
  TOOL_START: 1,
  TOOL_END: 2,
  SEARCH_START: 3,
  SEARCH_END: 4
}

const messages = ref([])
const isLoading = ref(false)
const isOnline = ref(false)
const messagesContainer = ref(null)
const eventSource = ref(null)
const contextId = ref(`context_${Date.now()}`)
const lastMessageId = ref(null)

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
    await axios.get(`${API_BASE_URL}/`)
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

const handleToolMessage = (botIndex, data) => {
  try {
    const contentObj = JSON.parse(data.content)
    
    if (data.type === MESSAGE_TYPES.TOOL_START || data.type === MESSAGE_TYPES.SEARCH_START) {
      messages.value[botIndex].thinking = `正在调用工具: ${contentObj.tool}`
      messages.value[botIndex].toolParams = contentObj.params
      messages.value[botIndex].toolName = contentObj.tool
    } else if (data.type === MESSAGE_TYPES.TOOL_END || data.type === MESSAGE_TYPES.SEARCH_END) {
      messages.value[botIndex].toolResult = contentObj.result
    }
  } catch (error) {
    console.error('解析工具消息失败:', error)
  }
}

const handleSend = async (text) => {
  messages.value.push({ role: 'user', content: text })
  
  const botIndex = messages.value.length
  messages.value.push({
    role: 'assistant',
    content: '',
    thinking: '正在思考...',
    finished: false,
    messageId: null,
    toolUsed: null,
    toolParams: null,
    toolResult: null
  })
  
  isLoading.value = true
  
  closeEventSource()
  
  try {
    const response = await axios.post(`${API_BASE_URL}/api/chat`, {
      content: text,
      uid: USER_ID,
      context_id: contextId.value,
      last_message_id: lastMessageId.value
    })
    
    const { message_id } = response.data
    
    messages.value[botIndex].messageId = message_id
    messages.value[botIndex].thinking = '正在接收响应...'
    
    await new Promise(resolve => setTimeout(resolve, 500))
    
    const eventSourceUrl = `${API_BASE_URL}/api/stream/${USER_ID}/${message_id}`
    eventSource.value = new EventSource(eventSourceUrl)
    
    eventSource.value.onmessage = (event) => {
      try {
        const rawData = event.data
        
        if (rawData.startsWith('data: ')) {
          const jsonStr = rawData.substring(6).trim()
          
          if (!jsonStr) return
          
          const data = JSON.parse(jsonStr)
          
          if (data.type !== undefined && data.type !== MESSAGE_TYPES.TEXT) {
            handleToolMessage(botIndex, data)
          } else if (data.content) {
            messages.value[botIndex].thinking = ''
            messages.value[botIndex].content += data.content
          }
          
          if (data.status && data.finish_reason) {
            messages.value[botIndex].finished = true
            messages.value[botIndex].thinking = ''
            lastMessageId.value = message_id
            closeEventSource()
          }
        }
      } catch (error) {
        console.error('解析SSE消息失败:', error, '原始数据:', event.data)
      }
    }
    
    eventSource.value.onerror = (error) => {
      console.error('SSE连接错误:', error)
      messages.value[botIndex].finished = true
      messages.value[botIndex].thinking = ''
      if (!messages.value[botIndex].content) {
        messages.value[botIndex].content = '抱歉，连接出现问题，请稍后重试。'
      }
      closeEventSource()
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
  const interval = setInterval(checkOnlineStatus, 5000)
  
  onUnmounted(() => {
    clearInterval(interval)
    closeEventSource()
  })
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
