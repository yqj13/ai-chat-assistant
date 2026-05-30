import axios from 'axios'
import { ElMessage } from 'element-plus'

const BASE_URL = 'http://localhost:8000/api'

const request = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

let loginModalInstance = null

export const setLoginModalInstance = (instance) => {
  loginModalInstance = instance
}

request.interceptors.request.use(
  (config) => {
    const userData = localStorage.getItem('user')
    if (userData) {
      try {
        const user = JSON.parse(userData)
        if (user.uid) {
          config.headers['X-UID'] = user.uid
        }
      } catch (e) {
        console.error('[Request] Failed to parse user data:', e)
      }
    }
    return config
  },
  (error) => {
    console.error('[Request] Request config error:', error)
    return Promise.reject(error)
  }
)

request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const { response } = error
    const status = response?.status
    const errorData = response?.data
    const errorMessage = errorData?.error || error.message || '请求失败'

    console.error('[Request] Response error:', {
      status,
      url: error.config?.url,
      method: error.config?.method,
      message: errorMessage,
      data: errorData
    })

    switch (status) {
      case 400:
        ElMessage.error(`请求参数错误: ${errorMessage}`)
        break
      case 401:
        ElMessage.warning('登录已过期，请重新登录')
        if (loginModalInstance) {
          loginModalInstance.open()
        }
        break
      case 403:
        ElMessage.error('没有权限访问该资源')
        break
      case 404:
        ElMessage.error('请求的资源不存在')
        break
      case 500:
      case 502:
      case 503:
        console.error('[Request] Server error:', {
          status,
          url: error.config?.url,
          detail: errorData
        })
        ElMessage.error('服务器错误，请稍后重试')
        break
      case 0:
        if (error.message.includes('timeout')) {
          ElMessage.error('请求超时，请检查网络连接')
        } else {
          ElMessage.error('网络连接失败，请检查网络')
        }
        break
      default:
        ElMessage.error(errorMessage)
    }

    return Promise.reject({
      status,
      message: errorMessage,
      data: errorData,
      isAuthError: status === 401
    })
  }
)

export const get = (url, params = {}, config = {}) => {
  return request.get(url, { params, ...config })
}

export const post = (url, data = {}, config = {}) => {
  return request.post(url, data, config)
}

export const put = (url, data = {}, config = {}) => {
  return request.put(url, data, config)
}

export const del = (url, config = {}) => {
  return request.delete(url, config)
}

export const upload = (url, formData, config = {}) => {
  return request.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    ...config
  })
}

export default request