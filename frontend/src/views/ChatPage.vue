<script setup>
import { ref, provide, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { chatApi } from '../api/chat'
import { userApi } from '../api/user'
import Sidebar from '../components/Sidebar.vue'
import ChatMessages from '../components/ChatMessages.vue'
import MessageInput from '../components/MessageInput.vue'
import { ChatStateManager, createUserMessage } from '../utils'
import { useChatStream } from '../composables/useChatStream'
import { useConversation } from '../composables/useConversation'

const router = useRouter()
const userStore = useUserStore()
const uid = computed(() => userStore.getUid())
const chatStateManager = computed(() => new ChatStateManager(uid.value))
const chatStream = useChatStream(uid, chatStateManager)
const conversation = useConversation(uid, chatStateManager)

const sidebarCollapsed = ref(false)
const sidebarWidth = computed(() => sidebarCollapsed.value ? 64 : 260)

const pendingPlaceholderId = ref(null)

const {
  conversations,
  currentConversation,
  messages,
  isLoadingMessages,
  loadConversations,
  selectConversation,
  createNewConversation,
  deleteConversation,
  updateConversationTitle,
  updateConversationLastMessage,
  getStoredConversationId,
  clearAll
} = conversation

const {
  eventSource,
  isStreaming,
  currentMessageId,
  lastSequence,
  safeJsonParse,
  close,
  createConnection,
  setStreamState,
  clearStreamState
} = chatStream

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const findMessageIndex = (messageId) => {
  return messages.value.findIndex(m => m.id === messageId)
}

const handleStreamMessage = (data) => {
  try {
    if (!data.message_id) return

    if (data.sequence) {
      lastSequence.value = data.sequence
      setStreamState(data.message_id, data.sequence)
    }

    if (data.status === true || data.finish_status === true) {
      isStreaming.value = false
      clearStreamState()

      const index = findMessageIndex(data.message_id)
      if (index !== -1) {
        messages.value[index] = {
          ...messages.value[index],
          loading: false,
          finished: true
        }

        if (currentConversation.value) {
          const finalMsg = messages.value[index]
          const finalText = (finalMsg.parts || []).filter(p => p.type === 'text').map(p => p.content).join('')
          updateConversationLastMessage(currentConversation.value.id, (finalText || '').substring(0, 50))

          const firstUser = messages.value.find(m => m.role === 'user')
          if (firstUser && currentConversation.value.title === '新对话') {
            const newTitle = (firstUser.content || '').substring(0, 20) || '新对话'
            updateConversationTitle(currentConversation.value.id, newTitle)
            userApi.updateSession(currentConversation.value.id, newTitle).catch(err => {
              console.error('更新会话标题失败:', err)
            })
          }
        }
        console.log('消息渲染:', messages.value[index])
      }
      return
    }

    if (data.message_id) {
      currentMessageId.value = data.message_id
      isStreaming.value = true
    }

    let index = findMessageIndex(data.message_id)

    if (index === -1 && pendingPlaceholderId.value) {
      index = findMessageIndex(pendingPlaceholderId.value)
      if (index !== -1) {
        messages.value[index] = {
          ...messages.value[index],
          id: data.message_id
        }
        pendingPlaceholderId.value = null
        currentMessageId.value = data.message_id
      }
    }

    if (index === -1 && data.message_id) {
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
        console.warn(`收到未知 message_id: ${data.message_id}，当前 pending: ${pendingPlaceholderId.value}，忽略`)
        return
      }
    }

    if (index === -1) return

    const existingMessage = messages.value[index]

    let newLoading = existingMessage.loading
    if (newLoading && (data.content || data.reasoning_content)) {
      newLoading = false
    }

    let newParts = existingMessage.parts ? [...existingMessage.parts] : []
    let newReasoningContent = existingMessage.reasoningContent || ''

    if (data.type === 0 || data.type === undefined) {
      if (data.reasoning_content) {
        newReasoningContent += data.reasoning_content
        messages.value[index].collapsed = false
        messages.value[index].thinking = true
      } else {
        messages.value[index].collapsed = true
        messages.value[index].thinking = false
      }

      if (data.content) {
        const lastPart = newParts.length > 0 ? newParts[newParts.length - 1] : null

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
      if (data.content) {
        try {
          const toolData = JSON.parse(data.content)

          if (data.type === 1 || data.type === 3) {
            newParts.push({
              type: 'tool_call',
              params: toolData,
              result: null,
              timestamp: Date.now(),
              collapsed: true
            })
          } else {
            const lastToolCall = newParts.findLast(p => p.type === 'tool_call' && p.result === null)
            if (lastToolCall) {
              lastToolCall.result = toolData
            } else {
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
          newParts.push({
            type: 'text',
            content: data.content,
            timestamp: Date.now()
          })
        }
      }
      messages.value[index].toolCallsCollapsed = false
    }

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

const handleSendMessage = async (msg) => {
  if (!uid.value) {
    console.error('用户未登录')
    return
  }

  const content = typeof msg === 'string' ? msg : msg.content
  const deepThinking = typeof msg === 'object' ? msg.deepThinking || false : false
  const webSearch = typeof msg === 'object' ? msg.webSearch || false : false

  if (!content.trim()) return

  if (!currentConversation.value) {
    await createNewConversation()
    if (!currentConversation.value) return
  }

  isStreaming.value = true

  const userMessage = createUserMessage(content, { deepThinking, webSearch })
  messages.value.push(userMessage)

  const placeholderId = 'pending_' + Date.now()
  pendingPlaceholderId.value = placeholderId

  const placeholderMessage = {
    id: placeholderId,
    role: 'assistant',
    parts: [],
    reasoningContent: '',
    timestamp: Date.now(),
    loading: true,
    finished: false
  }
  messages.value.push(placeholderMessage)

  try {
    const result = await chatApi.sendMessage(
      content.trim(),
      uid.value,
      currentConversation.value?.id || null,
      null,
      deepThinking,
      webSearch
    )

    if (result.message_id) {
      currentMessageId.value = result.message_id
      lastSequence.value = 0
      setStreamState(result.message_id, 0)

      const index = findMessageIndex(placeholderId)
      if (index !== -1) {
        messages.value[index] = {
          ...messages.value[index],
          id: result.message_id
        }
      }
      pendingPlaceholderId.value = null

      console.log(`发送消息成功，message_id: ${result.message_id}`)

      if (!eventSource.value || eventSource.value.readyState === EventSource.CLOSED) {
        createConnection(handleStreamMessage)
      }
    } else {
      const index = findMessageIndex(placeholderId)
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
    const index = findMessageIndex(placeholderId)
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

const handleLogout = async () => {
  clearAll()
  clearStreamState()
  messages.value = []
  pendingPlaceholderId.value = null
  close()
  userStore.logout()
}

onMounted(async () => {
  userStore.loadUserFromStorage()

  const storedState = chatStateManager.value.getStreamState()
  if (storedState && storedState.messageId) {
    console.log('检测到未完成的对话，尝试恢复')
    isStreaming.value = true
    currentMessageId.value = storedState.messageId
    lastSequence.value = storedState.sequence || 0
  }

  createConnection(handleStreamMessage)

  await loadConversations()
  if (conversations.value.length > 0) {
    const storedConvId = getStoredConversationId()
    let targetConv = null
    if (storedConvId) {
      targetConv = conversations.value.find(c => c.id === storedConvId)
    }
    if (!targetConv) {
      targetConv = conversations.value[0]
    }
    await selectConversation(targetConv)
  }
})

onUnmounted(() => {
  close()
})

watch(() => userStore.isLoggedIn, async (loggedIn) => {
  if (!loggedIn) {
    userStore.openLoginModal()
  } else {
    await loadConversations()
    if (conversations.value.length > 0 && !currentConversation.value) {
      await selectConversation(conversations.value[0])
    }
    if (!eventSource.value) {
      createConnection(handleStreamMessage)
    }
  }
})

provide('sidebarCollapsed', sidebarCollapsed)
provide('toggleSidebar', toggleSidebar)
provide('handleLogout', handleLogout)
provide('currentUser', userStore.user)
</script>

<template>
  <div class="chat-page">
    
    <Sidebar
      :collapsed="sidebarCollapsed"
      :conversations="conversations"
      :current-conversation="currentConversation"
      :current-user="userStore.user"
      @toggle="toggleSidebar"
      @select="selectConversation"
      @new="createNewConversation"
      @delete="deleteConversation"
      @logout="handleLogout"
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
  width: 100vw;
  overflow: hidden;
  background-color: #f5f5f5;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: margin-left 0.3s ease;
  position: relative;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
}

.chat-message-block {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #666;
  text-align: center;
}

.empty-state h2 {
  margin-bottom: 8px;
  color: #333;
}

.empty-state p {
  color: #999;
  font-size: 14px;
}

.empty-icon {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  color: #ddd;
}
</style>
