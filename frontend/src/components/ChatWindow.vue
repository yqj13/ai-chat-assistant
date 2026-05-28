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
const contextId = ref(null)
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
      model: 'qwen-7b-chat',
      messages: [{ role: 'user', content: text }],
      temperature: 0.3,
      context_id: contextId.value,
      last_message_id: lastMessageId.value
    })
    
    const botIndex = messages.value.length - 1
    const reply = response.data.choices[0].message.content
    
    messages.value[botIndex].content = reply
    messages.value[botIndex].finished = true
    messages.value[botIndex].thinking = ''
    messages.value[botIndex].messageId = response.data.id
    
    if (response.data.choices[0].finish_reason === 'tool_calls') {
      messages.value[botIndex].toolUsed = response.data.choices[0].message.tool_calls?.[0]?.function.name
    }
    
    if (response.data.context_id) {
      contextId.value = response.data.context_id
    }
    
    lastMessageId.value = response.data.id
    
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

const handleSendStream = async (text) => {
  messages.value.push({ role: 'user', content: text })
  
  const botIndex = messages.value.length
  messages.value.push({
    role: 'assistant',
    content: '',
    thinking: '正在分析问题...',
    finished: false,
    messageId: null
  })
  
  isLoading.value = true
  
  closeEventSource()
  
  try {
    const response = await fetch('http://localhost:8000/v1/chat/completions/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'qwen-7b-chat',
        messages: [{ role: 'user', content: text }],
        temperature: 0.3,
        context_id: contextId.value,
        last_message_id: lastMessageId.value
      })
    })
    
    if (!response.body) {
      throw new Error('Response body is null')
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    
    while (true) {
      const { done, value } = await reader.read()
      
      if (done) {
        break
      }
      
      const text = decoder.decode(value, { stream: true })
      const lines = text.split('\n')
      
      for (const line of lines) {
        if (line.trim()) {
          try {
            const data = JSON.parse(line.replace(/^data: /, ''))
            
            if (data.choices && data.choices[0] && data.choices[0].delta) {
              const delta = data.choices[0].delta
              
              if (delta.content) {
                messages.value[botIndex].thinking = ''
                messages.value[botIndex].content += delta.content
              }
              
              if (data.context_id) {
                contextId.value = data.context_id
              }
              
              if (data.message_id) {
                messages.value[botIndex].messageId = data.message_id
                lastMessageId.value = data.message_id
              }
              
              if (data.choices[0].finish_reason === 'stop') {
                messages.value[botIndex].finished = true
              }
            }
          } catch (e) {
            console.error('解析流式消息失败:', e)
          }
        }
      }
    }
    
    messages.value[botIndex].finished = true
    
  } catch (error) {
    console.error('流式请求失败:', error)
    const botIndex = messages.value.length - 1
    messages.value[botIndex].content = '抱歉，流式请求失败，请稍后重试。'
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