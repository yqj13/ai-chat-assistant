import { ref } from 'vue'
import { userApi } from '../api/user'
import { ChatStateManager, mapServerMessagesToLocal } from '../utils'

export function useConversation(uid, chatStateManager) {
  const conversations = ref([])
  const currentConversation = ref(null)
  const isLoadingMessages = ref(false)
  const messages = ref([])

  const loadConversations = async () => {
    if (!uid.value) return
    try {
      const list = await userApi.getUserSessions(uid.value)
      conversations.value = (list || []).map(s => ({
        id: s.session_id,
        title: s.title || '新对话',
        lastMessage: '',
        timestamp: s.updated_at ? new Date(s.updated_at).getTime() : Date.now()
      }))
    } catch (e) {
      console.error('加载会话列表失败:', e)
      conversations.value = []
    }
  }

  const loadConversationMessages = async (conv) => {
    if (!conv?.id) {
      messages.value = []
      return
    }
    isLoadingMessages.value = true
    try {
      const serverMessages = await userApi.getSessionMessages(conv.id)
      messages.value = mapServerMessagesToLocal(serverMessages || [])
      const lastAssistant = [...messages.value].reverse().find(m => m.role === 'assistant')
      if (lastAssistant) {
        const lastText = (lastAssistant.parts || []).filter(p => p.type === 'text').map(p => p.content).join('')
        conv.lastMessage = (lastText || '').substring(0, 50)
      }
    } catch (e) {
      console.error('加载会话消息失败:', e)
      messages.value = []
    } finally {
      isLoadingMessages.value = false
    }
  }

  const selectConversation = async (conv) => {
    if (currentConversation.value?.id === conv.id) return
    currentConversation.value = conv
    chatStateManager?.value?.setConversationId?.(conv.id)
    await loadConversationMessages(conv)
  }

  const createNewConversation = async () => {
    if (!uid.value) return
    try {
      const session = await userApi.createSession(uid.value, null, '新对话')
      const newConv = {
        id: session.session_id,
        title: session.title || '新对话',
        lastMessage: '',
        timestamp: session.created_at ? new Date(session.created_at).getTime() : Date.now()
      }
      conversations.value.unshift(newConv)
      currentConversation.value = newConv
      chatStateManager?.value?.setConversationId?.(newConv.id)
      messages.value = []
      return newConv
    } catch (e) {
      console.error('创建会话失败:', e)
      return null
    }
  }

  const deleteConversation = async (conv) => {
    if (!conv?.id) return
    try {
      await userApi.deleteSession(conv.id)
      const idx = conversations.value.findIndex(c => c.id === conv.id)
      if (idx !== -1) conversations.value.splice(idx, 1)
      if (currentConversation.value?.id === conv.id) {
        const next = conversations.value[0] || null
        currentConversation.value = next
        if (next) {
          chatStateManager?.value?.setConversationId?.(next.id)
          await loadConversationMessages(next)
        } else {
          chatStateManager?.value?.setConversationId?.(null)
          messages.value = []
        }
      }
    } catch (e) {
      console.error('删除会话失败:', e)
    }
  }

  const updateConversationTitle = (convId, title) => {
    const conv = conversations.value.find(c => c.id === convId)
    if (conv) {
      conv.title = title
    }
  }

  const updateConversationLastMessage = (convId, lastMessage) => {
    const conv = conversations.value.find(c => c.id === convId)
    if (conv) {
      conv.lastMessage = lastMessage
      conv.timestamp = Date.now()
      const idx = conversations.value.findIndex(c => c.id === convId)
      if (idx > 0) {
        const [item] = conversations.value.splice(idx, 1)
        conversations.value.unshift(item)
      }
    }
  }

  const getStoredConversationId = () => {
    return chatStateManager?.value?.getConversationId?.() || null
  }

  const clearAll = () => {
    conversations.value = []
    currentConversation.value = null
    messages.value = []
    chatStateManager?.value?.setConversationId?.(null)
  }

  return {
    conversations,
    currentConversation,
    isLoadingMessages,
    messages,
    loadConversations,
    loadConversationMessages,
    selectConversation,
    createNewConversation,
    deleteConversation,
    updateConversationTitle,
    updateConversationLastMessage,
    getStoredConversationId,
    clearAll
  }
}
