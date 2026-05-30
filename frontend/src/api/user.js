import { get, post } from '../utils/request'

export const userApi = {
  register: (username, password) => {
    return post('/user/register', { username, password })
  },

  login: (username, password) => {
    return post('/user/login', { username, password })
  },

  loginByUid: (uid, username = null) => {
    return post('/user/login/uid', { uid, username })
  },

  getUserInfo: (uid) => {
    return get(`/user/${uid}`)
  },

  getUserSessions: (uid) => {
    return get(`/sessions/${uid}`)
  },

  createSession: (uid, sessionId = null, title = null) => {
    return post('/session', { uid, session_id: sessionId, title })
  },

  getSession: (sessionId) => {
    return get(`/session/${sessionId}`)
  },

  updateSession: (sessionId, title) => {
    return post(`/session/${sessionId}`, { title })
  },

  deleteSession: (sessionId) => {
    return post(`/session/${sessionId}`)
  },

  getSessionMessages: (sessionId, limit = null) => {
    return get(`/messages/${sessionId}`, { limit })
  },

  deleteMessage: (messageId) => {
    return post(`/message/${messageId}`)
  }
}

export default userApi