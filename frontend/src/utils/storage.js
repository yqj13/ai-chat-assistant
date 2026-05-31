export const storage = {
  get(key, defaultValue = null) {
    try {
      const data = localStorage.getItem(key)
      return data ? JSON.parse(data) : defaultValue
    } catch (e) {
      console.error(`读取 localStorage key "${key}" 失败:`, e)
      return defaultValue
    }
  },

  set(key, value) {
    try {
      if (value === null || value === undefined) {
        localStorage.removeItem(key)
      } else {
        localStorage.setItem(key, JSON.stringify(value))
      }
      return true
    } catch (e) {
      console.error(`写入 localStorage key "${key}" 失败:`, e)
      return false
    }
  },

  remove(key) {
    try {
      localStorage.removeItem(key)
      return true
    } catch (e) {
      console.error(`删除 localStorage key "${key}" 失败:`, e)
      return false
    }
  },

  clear() {
    try {
      localStorage.clear()
      return true
    } catch (e) {
      console.error('清空 localStorage 失败:', e)
      return false
    }
  }
}

export class ChatStateManager {
  constructor(uid) {
    this.uid = uid
  }

  get stateKey() {
    return `chat_state_${this.uid}`
  }

  get convKey() {
    return `chat_conv_${this.uid}`
  }

  getStreamState() {
    return storage.get(this.stateKey)
  }

  setStreamState(messageId, sequence) {
    if (messageId) {
      storage.set(this.stateKey, {
        messageId,
        sequence: sequence || 0
      })
    } else {
      storage.remove(this.stateKey)
    }
  }

  clearStreamState() {
    storage.remove(this.stateKey)
  }

  getConversationId() {
    const data = storage.get(this.convKey)
    return data?.conversationId || null
  }

  setConversationId(convId) {
    if (convId) {
      storage.set(this.convKey, { conversationId: convId })
    } else {
      storage.remove(this.convKey)
    }
  }

  clearConversationId() {
    storage.remove(this.convKey)
  }

  clearAll() {
    this.clearStreamState()
    this.clearConversationId()
  }
}
