import { ref } from 'vue'

export function useChatStream(uid, chatStateManager) {
  const eventSource = ref(null)
  const isStreaming = ref(false)
  const currentMessageId = ref(null)
  const lastSequence = ref(0)
  const reconnectAttempts = ref(0)
  const reconnectDelay = ref(1000)
  const reconnectTimer = ref(null)
  const maxReconnectAttempts = 5

  const resetReconnectState = () => {
    reconnectAttempts.value = 0
    reconnectDelay.value = 1000
    if (reconnectTimer.value) {
      clearTimeout(reconnectTimer.value)
      reconnectTimer.value = null
    }
  }

  const scheduleReconnect = (onReconnect = null) => {
    if (reconnectAttempts.value >= maxReconnectAttempts) {
      console.error(`已达到最大重连次数 (${maxReconnectAttempts})，停止重连`)
      resetReconnectState()
      return
    }
    const delayMs = reconnectDelay.value
    console.log(`计划在 ${delayMs}ms 后重连...`)
    reconnectTimer.value = setTimeout(() => {
      reconnectAttempts.value++
      reconnectDelay.value = Math.min(reconnectDelay.value * 2, 30000)
      if (onReconnect) {
        onReconnect()
      }
    }, delayMs)
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

  const close = () => {
    if (eventSource.value) {
      eventSource.value.close()
      eventSource.value = null
    }
    if (reconnectTimer.value) {
      clearTimeout(reconnectTimer.value)
      reconnectTimer.value = null
    }
    resetReconnectState()
    isStreaming.value = false
  }

  const createConnection = (messageHandler, onReconnect = null) => {
    if (!uid.value) {
      console.error('用户未登录，无法建立SSE连接')
      return null
    }

    if (eventSource.value) {
      eventSource.value.close()
      eventSource.value = null
    }

    let url = `http://localhost:8000/api/stream/${uid.value}`
    const params = new URLSearchParams()

    const storedState = chatStateManager?.value?.getStreamState?.()
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

    const source = new EventSource(url)

    source.onopen = () => {
      console.log('SSE 连接已建立')
      resetReconnectState()
    }

    source.onmessage = (event) => {
      try {
        const data = safeJsonParse(event.data)
        if (!data) return
        messageHandler(data)
      } catch (e) {
        console.error('处理消息失败:', e)
      }
    }

    source.onerror = (error) => {
      console.error('SSE 连接错误:', error)
      source.close()
      eventSource.value = null
      if (chatStateManager?.value?.setStreamState && currentMessageId.value && isStreaming.value) {
        chatStateManager.value.setStreamState(currentMessageId.value, lastSequence.value)
        scheduleReconnect(() => {
          createConnection(messageHandler, onReconnect)
        })
      }
    }

    eventSource.value = source
    return source
  }

  const setStreamState = (messageId, sequence) => {
    currentMessageId.value = messageId
    lastSequence.value = sequence
    if (chatStateManager?.value?.setStreamState) {
      chatStateManager.value.setStreamState(messageId, sequence)
    }
  }

  const clearStreamState = () => {
    currentMessageId.value = null
    lastSequence.value = 0
    isStreaming.value = false
    if (chatStateManager?.value?.setStreamState) {
      chatStateManager.value.setStreamState(null, 0)
    }
  }

  return {
    eventSource,
    isStreaming,
    currentMessageId,
    lastSequence,
    reconnectAttempts,
    reconnectDelay,
    reconnectTimer,
    maxReconnectAttempts,
    resetReconnectState,
    scheduleReconnect,
    safeJsonParse,
    close,
    createConnection,
    setStreamState,
    clearStreamState
  }
}
