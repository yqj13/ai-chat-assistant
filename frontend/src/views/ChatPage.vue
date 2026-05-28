<script setup>
import { ref, provide, computed, onMounted, onUnmounted } from 'vue'
import Sidebar from '../components/Sidebar.vue'
import ChatMessages from '../components/ChatMessages.vue'
import MessageInput from '../components/MessageInput.vue'

const sidebarCollapsed = ref(false)
const currentConversation = ref(null)
const messages = ref([])
const isStreaming = ref(false)
const currentMessageId = ref(null)
const uid = ref('user_' + Date.now())

const sidebarWidth = computed(() => sidebarCollapsed.value ? 64 : 260)

const conversations = ref([
  { id: 'conv1', title: '新对话', messages: [], lastMessage: '', timestamp: Date.now() },
  { id: 'conv2', title: '技术咨询', messages: [], lastMessage: '如何使用Python进行数据分析？', timestamp: Date.now() - 3600000 },
  { id: 'conv3', title: '项目讨论', messages: [], lastMessage: '关于前端架构的一些想法', timestamp: Date.now() - 7200000 }
])

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const selectConversation = (conv) => {
  currentConversation.value = conv
  messages.value = conv.messages || []
}

const createNewConversation = () => {
  const newConv = {
    id: 'conv_' + Date.now(),
    title: '新对话',
    messages: [],
    lastMessage: '',
    timestamp: Date.now()
  }
  conversations.value.unshift(newConv)
  selectConversation(newConv)
}

const handleSendMessage = async (content) => {
  if (!content.trim()) return
  
  isStreaming.value = true
  
  const userMessage = {
    id: 'msg_' + Date.now(),
    role: 'user',
    content: content.trim(),
    timestamp: Date.now()
  }
  
  messages.value.push(userMessage)
  
  try {
    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        content: content.trim(),
        uid: uid.value,
        context_id: currentConversation.value?.id || uid.value,
        last_message_id: currentMessageId.value
      })
    })
    
    const data = await response.json()
    currentMessageId.value = data.message_id
    
    await listenToStream(data.message_id)
    
  } catch (error) {
    console.error('发送消息失败:', error)
    const errorMessage = {
      id: 'msg_' + Date.now(),
      role: 'assistant',
      content: '发送消息失败，请稍后重试',
      timestamp: Date.now()
    }
    messages.value.push(errorMessage)
    isStreaming.value = false
  }
}

const safeJsonParse = (input, fallback = null) => {
  if (!input) return fallback
  
  try {
    let data = input
    
    if (typeof data === 'string') {
      data = data.trim()
      
      if (data.startsWith('data:')) {
        data = data.substring(5).trim()
      }
      
      if (data.startsWith('{') || data.startsWith('[')) {
        return JSON.parse(data)
      }
    }
    
    return fallback
  } catch (error) {
    console.warn('JSON 解析失败:', error)
    return fallback
  }
}

const listenToStream = async (messageId) => {
  return new Promise((resolve) => {
    const eventSource = new EventSource(`http://localhost:8000/api/stream/${uid.value}/${messageId}`)
    
    let assistantMessage = null
    
    eventSource.onmessage = (event) => {
      try {
        const data = safeJsonParse(event.data)
        
        if (!data) {
          return
        }
        
        if (!assistantMessage) {
          assistantMessage = {
            id: data.message_id || messageId,
            role: 'assistant',
            content: '',
            timestamp: Date.now()
          }
          messages.value.push(assistantMessage)
        }
        
        if (data.content) {
          assistantMessage.content += data.content
        }
        
        if (data.status === true) {
          eventSource.close()
          isStreaming.value = false
          if (currentConversation.value) {
            currentConversation.value.lastMessage = assistantMessage.content.substring(0, 50) + (assistantMessage.content.length > 50 ? '...' : '')
            currentConversation.value.timestamp = Date.now()
            currentConversation.value.messages = messages.value
          }
          resolve()
        }
      } catch (error) {
        console.error('解析消息失败:', error)
      }
    }
    
    eventSource.onerror = (error) => {
      console.error('Stream error:', error)
      eventSource.close()
      isStreaming.value = false
      resolve()
    }
  })
}

onMounted(() => {
  if (conversations.value.length > 0) {
    selectConversation(conversations.value[0])
  }
})

onUnmounted(() => {
  if (currentMessageId.value) {
    fetch(`http://localhost:8000/api/user/${uid.value}`, {
      method: 'DELETE'
    }).catch(() => {})
  }
})

provide('sidebarCollapsed', sidebarCollapsed)
provide('toggleSidebar', toggleSidebar)
</script>

<template>
  <div class="chat-page">
    <Sidebar
      :collapsed="sidebarCollapsed"
      :conversations="conversations"
      :current-conversation="currentConversation"
      @toggle="toggleSidebar"
      @select="selectConversation"
      @new="createNewConversation"
    />
    
    <div 
      class="chat-main"
      :style="{ marginLeft: sidebarWidth + 'px' }"
    >
      <div v-if="currentConversation" class="chat-container">
        <ChatMessages 
          :messages="messages" 
          :is-streaming="isStreaming"
        />
        
        <MessageInput 
          @send="handleSendMessage"
          :disabled="isStreaming"
        />
      </div>
      
      <div v-else class="empty-state">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </div>
        <h2>开始新对话</h2>
        <p>点击左侧"新建对话"按钮开始与AI聊天</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
  transition: margin-left 0.3s ease;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
}

.empty-icon {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  color: #1890ff;
}

.empty-icon svg {
  width: 100%;
  height: 100%;
}

.empty-state h2 {
  margin-bottom: 8px;
  font-size: 18px;
  color: #333;
}

.empty-state p {
  font-size: 14px;
}

@media (max-width: 768px) {
  .chat-main {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 10;
    margin-left: 0 !important;
  }
  
  .chat-page {
    position: relative;
  }
}
</style>