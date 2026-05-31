import { get, post } from '../utils/request'

export class ChatAPI {
  static sendMessage(content, uid, contextId = null, lastMessageId = null, deepThinking = false, webSearch = false) {
    return post('/chat', {
      content,
      uid,
      context_id: contextId,
      last_message_id: lastMessageId,
      deep_thinking: deepThinking,
      web_search: webSearch
    })
  }

  static getStreamUrl(uid, messageId = null, lastSequence = 0) {
    let url = `/stream/${uid}`
    const params = new URLSearchParams()
    if (messageId) {
      params.set('message_id', messageId)
      params.set('last_sequence', lastSequence.toString())
      url += `?${params.toString()}`
    }
    return `http://localhost:8000/api${url}`
  }

  static cleanupUser(uid) {
    return post(`/user/${uid}`)
  }

  static cleanupMessage(uid, messageId) {
    return post(`/message/${uid}/${messageId}`)
  }
}

export class AguiChatAPI {
  static sendMessage(content, uid, runId = null) {
    return post('/agui/chat', { content, uid, run_id: runId })
  }

  static getStreamUrl(uid, messageId = null, lastSequence = 0, model = null, temperature = null) {
    let url = '/agui/stream'
    const params = new URLSearchParams()
    params.set('uid', uid)
    if (messageId) {
      params.set('message_id', messageId)
      params.set('last_sequence', lastSequence.toString())
    }
    if (model) {
      params.set('model', model)
    }
    if (temperature !== null) {
      params.set('temperature', temperature.toString())
    }
    return `http://localhost:8000/api${url}?${params.toString()}`
  }

  static cleanupUser(uid) {
    return post(`/agui/user/${uid}`)
  }

  static cleanupMessage(uid, messageId) {
    return post(`/agui/message/${uid}/${messageId}`)
  }
}

export const chatApi = ChatAPI
export const aguiChatApi = AguiChatAPI

export default chatApi
