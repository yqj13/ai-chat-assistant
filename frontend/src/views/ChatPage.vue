<script setup>
import { ref, provide, computed, onMounted, onUnmounted, nextTick } from 'vue'
import Sidebar from '../components/Sidebar.vue'
import ChatMessages from '../components/ChatMessages.vue'
import MessageInput from '../components/MessageInput.vue'

const sidebarCollapsed = ref(false)
const currentConversation = ref(null)
const messages = ref([])
const isStreaming = ref(false)
const currentMessageId = ref(null)
const lastSequence = ref(0)
const uid = ref('1')

const eventSource = ref(null)

// 新增：记录占位消息的临时 id，用于在 SSE 中匹配
const pendingPlaceholderId = ref(null)

// 重连策略
const reconnectAttempts = ref(0)
const maxReconnectAttempts = 5
const reconnectDelay = ref(1000)
const reconnectTimer = ref(null)

const localStorageKey = ref('1')

const getStoredState = () => {
  try {
    const data = localStorage.getItem(localStorageKey.value)
    return data ? JSON.parse(data) : null
  } catch (e) {
    console.error('读取 localStorage 失败:', e)
    return null
  }
}

const setStoredState = (messageId, sequence) => {
  try {
    if (messageId) {
      localStorage.setItem(localStorageKey.value, JSON.stringify({
        messageId,
        sequence: sequence || 0
      }))
    } else {
      localStorage.removeItem(localStorageKey.value)
    }
  } catch (e) {
    console.error('写入 localStorage 失败:', e)
  }
}

const sidebarWidth = computed(() => sidebarCollapsed.value ? 64 : 260)

const conversations = ref([
  { id: 'conv1', title: '新对话', messages: [], lastMessage: '', timestamp: Date.now() }
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

const findMessageIndex = (messageId) => {
  return messages.value.findIndex(m => m.id === messageId)
}

const handleSendMessage = async (message) => {
  const content = typeof message === 'string' ? message : message.content
  const deepThinking = typeof message === 'object' ? message.deepThinking || false : false
  const webSearch = typeof message === 'object' ? message.webSearch || false : false

  if (!content.trim()) return

  isStreaming.value = true

  // 1. 添加用户消息
  const userMessage = {
    id: 'msg_' + Date.now(),
    role: 'user',
    content: content.trim(),
    deepThinking,
    webSearch,
    timestamp: Date.now()
  }
  messages.value.push(userMessage)

  // 2. 立即添加一条空的助手消息（占位）
  const placeholderMessageId = 'pending_' + Date.now()
  pendingPlaceholderId.value = placeholderMessageId  // ✅ 记录临时 id

  const assistantMessage = {
    id: placeholderMessageId,
    role: 'assistant',
    parts: [],
    reasoningContent: '',
    timestamp: Date.now(),
    loading: true,
    finished: false
  }
  messages.value.push(assistantMessage)

  try {
    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: content.trim(),
        uid: uid.value,
        context_id: currentConversation.value?.id || null,
        last_message_id: null,
        deep_thinking: deepThinking,
        web_search: webSearch
      })
    })

    if (response.ok) {
      const result = await response.json()
      currentMessageId.value = result.message_id
      lastSequence.value = 0
      setStoredState(result.message_id, 0)

      // 3. 替换占位消息的 id
      const index = findMessageIndex(placeholderMessageId)
      if (index !== -1) {
        messages.value[index] = {
          ...messages.value[index],
          id: result.message_id
        }
      }
      pendingPlaceholderId.value = null  // ✅ 清除临时 id

      console.log(`发送消息成功，message_id: ${result.message_id}`)

      // 确保 SSE 连接存在
      if (!eventSource.value || eventSource.value.readyState === EventSource.CLOSED) {
        createStreamConnection()
      }
    } else {
      const index = findMessageIndex(placeholderMessageId)
      if (index !== -1) {
        messages.value[index] = {
          ...messages.value[index],
          content: '请求失败，请稍后重试',
          loading: false,
          finished: true
        }
      }
      pendingPlaceholderId.value = null
      isStreaming.value = false
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    const index = findMessageIndex(placeholderMessageId)
    if (index !== -1) {
      messages.value[index] = {
        ...messages.value[index],
        content: '网络连接失败，请检查网络后重试',
        loading: false,
        finished: true
      }
    }
    pendingPlaceholderId.value = null
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

const resetReconnectState = () => {
  reconnectAttempts.value = 0
  reconnectDelay.value = 1000
  if (reconnectTimer.value) {
    clearTimeout(reconnectTimer.value)
    reconnectTimer.value = null
  }
}

const scheduleReconnect = () => {
  if (reconnectAttempts.value >= maxReconnectAttempts) {
    console.error('已达到最大重连次数，停止尝试')
    isStreaming.value = false

    if (currentMessageId.value) {
      const index = findMessageIndex(currentMessageId.value)
      if (index !== -1) {
        messages.value[index] = {
          ...messages.value[index],
          content: messages.value[index].content + '\n\n[连接中断，回复未完成]',
          loading: false,
          finished: true
        }
      }
    }
    return
  }

  const delay = reconnectDelay.value
  console.log(`尝试重连 (第 ${reconnectAttempts.value + 1} 次)，等待 ${delay}ms`)

  reconnectTimer.value = setTimeout(() => {
    reconnectAttempts.value++
    reconnectDelay.value = Math.min(reconnectDelay.value * 2, 30000)
    createStreamConnection()
  }, delay)
}

const createStreamConnection = () => {
  if (eventSource.value) {
    eventSource.value.close()
    eventSource.value = null
  }

  let url = `http://localhost:8000/api/stream/${uid.value}`
  const params = new URLSearchParams()

  const storedState = getStoredState()
  const msgId = currentMessageId.value || storedState?.messageId
  const seq = lastSequence.value || storedState?.sequence || 0

  if (msgId) {
    params.set('message_id', msgId)
    params.set('last_sequence', seq.toString())
    currentMessageId.value = msgId
    lastSequence.value = seq
    console.log(`连接 SSE，message_id: ${msgId}, last_sequence: ${seq}`)
  }

  const queryString = params.toString()
  if (queryString) {
    url += `?${queryString}`
  }

  eventSource.value = new EventSource(url)

  eventSource.value.onopen = () => {
    console.log('SSE 连接已建立')
    resetReconnectState()
  }

  eventSource.value.onmessage = (event) => {
    try {
      const data = safeJsonParse(event.data)
      if (!data) return

      // ✅ 忽略没有 message_id 的数据（心跳等）
      if (!data.message_id) return

      // 更新 sequence
      if (data.sequence) {
        lastSequence.value = data.sequence
        setStoredState(data.message_id, data.sequence)
      }

      // 消息完成
      if (data.status === true || data.finish_status === true) {
        isStreaming.value = false
        currentMessageId.value = null
        lastSequence.value = 0
        setStoredState(null, 0)


        const index = findMessageIndex(data.message_id)
        if (index !== -1) {
          messages.value[index] = {
            ...messages.value[index],
            loading: false,
            finished: true
          }

          if (currentConversation.value) {
            currentConversation.value.lastMessage = messages.value[index].content.substring(0, 50)
            currentConversation.value.timestamp = Date.now()
            currentConversation.value.messages = [...messages.value]
          }
          console.log('消息渲染:', messages.value[index])
        }
        return
      }

      if (data.message_id) {
        currentMessageId.value = data.message_id
        isStreaming.value = true
      }

      // ✅ 核心修复：查找消息时，同时检查正式 id 和占位 id
      let index = findMessageIndex(data.message_id)

      // 如果通过 message_id 找不到，检查是否有正在等待的占位消息
      // （处理 SSE 在 fetch 返回前就推送数据的竞态情况）
      if (index === -1 && pendingPlaceholderId.value) {
        index = findMessageIndex(pendingPlaceholderId.value)
        if (index !== -1) {
          // 将占位消息的 id 更新为真实 message_id
          messages.value[index] = {
            ...messages.value[index],
            id: data.message_id
          }
          pendingPlaceholderId.value = null
          currentMessageId.value = data.message_id
        }
      }

      // ✅ 只有在断点续传场景（无占位消息）才创建新消息
      if (index === -1 && data.message_id) {
        // 再次确认：确保不是因为占位消息尚未创建
        // 只有当没有 pending 状态时才新建（真正的断点续传场景）
        if (!pendingPlaceholderId.value) {
          messages.value.push({
            id: data.message_id,
            role: 'assistant',
            parts: [],
            reasoningContent: '',
            timestamp: Date.now(),
            loading: true,
            finished: false
          })
          index = messages.value.length - 1
        } else {
          // 有 pending 但 id 不匹配，说明是旧消息的残留数据，忽略
          console.warn(`收到未知 message_id: ${data.message_id}，当前 pending: ${pendingPlaceholderId.value}，忽略`)
          return
        }
      }

      if (index === -1) return

      const existingMessage = messages.value[index]

      // 收到内容时关闭 loading
      let newLoading = existingMessage.loading
      if (newLoading && (data.content || data.reasoning_content)) {
        newLoading = false
      }

      // 处理内容 - 按顺序添加到 parts 数组
      let newParts = existingMessage.parts ? [...existingMessage.parts] : []
      let newReasoningContent = existingMessage.reasoningContent || ''

      if (data.type === 0 || data.type === undefined) {
        // 普通文本内容
        if (data.reasoning_content) {
          newReasoningContent += data.reasoning_content
          messages.value[index].collapsed = false
          messages.value[index].thinking = true
        } else {
          messages.value[index].collapsed = true
          messages.value[index].thinking = false
        }
        
        if (data.content) {
          // 查找最后一个 part 的类型
          const lastPart = newParts.length > 0 ? newParts[newParts.length - 1] : null
          
          // 如果最后一个 part 是文本，才追加；否则创建新的文本 part
          if (lastPart && lastPart.type === 'text') {
            lastPart.content += data.content
          } else {
            newParts.push({
              type: 'text',
              content: data.content,
              timestamp: Date.now()
            })
          }
        }
        messages.value[index].toolCallsCollapsed = true
      } else {
        // 工具调用内容
        if (data.content) {
          try {
            const toolData = JSON.parse(data.content)
            
            if (data.type === 1 || data.type === 3) {
              // 工具开始调用
              newParts.push({
                type: 'tool_call',
                params: toolData,
                result: null,
                timestamp: Date.now(),
                collapsed: true
              })
            } else {
              // 工具执行完成，找到最近的未配对的 tool_call 并填入结果
              const lastToolCall = newParts.findLast(p => p.type === 'tool_call' && p.result === null)
              if (lastToolCall) {
                lastToolCall.result = toolData
              } else {
                // 如果没有找到对应的 tool_start，直接创建 tool_call
                newParts.push({
                  type: 'tool_call',
                  params: null,
                  result: toolData,
                  timestamp: Date.now(),
                  collapsed: true
                })
              }
            }
          } catch (e) {
            // 如果解析失败，当作普通文本处理
            newParts.push({
              type: 'text',
              content: data.content,
              timestamp: Date.now()
            })
          }
        }
        messages.value[index].toolCallsCollapsed = false
      }

      // 替换整个对象触发响应式
      messages.value[index] = {
        ...existingMessage,
        parts: newParts,
        reasoningContent: newReasoningContent,
        loading: newLoading
      }

      console.log('消息渲染:', messages.value[index])

    } catch (error) {
      console.error('处理消息失败:', error)
    }
  }

  eventSource.value.onerror = (error) => {
    console.error('SSE 连接错误:', error)

    if (eventSource.value) {
      eventSource.value.close()
      eventSource.value = null
    }

    if (isStreaming.value && currentMessageId.value) {
      setStoredState(currentMessageId.value, lastSequence.value)
      scheduleReconnect()
    }
  }
}

onMounted(() => {
  // 修复：只恢复状态，不创建占位消息
  // 占位消息应在 SSE 收到数据时按需创建（断点续传场景）
  const storedState = getStoredState()
  if (storedState && storedState.messageId) {
    console.log('检测到未完成的对话，尝试恢复')
    isStreaming.value = true
    currentMessageId.value = storedState.messageId
    lastSequence.value = storedState.sequence || 0
    scheduleReconnect()
  }

  createStreamConnection()

  if (conversations.value.length > 0) {
    selectConversation(conversations.value[0])
  }
})

onUnmounted(() => {
  if (eventSource.value) {
    eventSource.value.close()
    eventSource.value = null
  }
  if (reconnectTimer.value) {
    clearTimeout(reconnectTimer.value)
    reconnectTimer.value = null
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
        <div class="chat-message-block">
          <ChatMessages
            :messages="messages"
            :is-streaming="isStreaming"
            :current-streaming-id="currentMessageId"
          />
        </div>

        <MessageInput
          @send="handleSendMessage"
          :isStreaming="isStreaming"
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
  overflow: hidden;
}

.chat-message-block {
  flex: 1;
  overflow-y: auto;
  min-height: 0; /* ✅ 关键：flex子元素溢出修复 */
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