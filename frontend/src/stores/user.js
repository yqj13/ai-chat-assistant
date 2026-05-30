import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userApi } from '../api/user'
import { useLogin } from '../composables/useLogin'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const isLoggedIn = computed(() => !!user.value?.uid)

  const openLoginModal = (onSuccess) => {
    const login = useLogin()
    login.open({
      onConfirm: (data) => {
        user.value = data
        localStorage.setItem('user', JSON.stringify(data))
        if (typeof onSuccess === 'function') {
          onSuccess(data)
        }
      }
    })
  }

  const login = async (username, password) => {
    try {
      const data = await userApi.login(username, password)
      user.value = data
      localStorage.setItem('user', JSON.stringify(data))
      return { success: true, data }
    } catch (error) {
      return { success: false, error: error.message || '登录失败', isAuthError: error.isAuthError }
    }
  }

  const auth = async (username, password) => {
    try {
      const data = await userApi.auth(username, password)
      user.value = data
      localStorage.setItem('user', JSON.stringify(data))
      return { success: true, data, isNewUser: !!data?.is_new_user }
    } catch (error) {
      return { success: false, error: error.message || '操作失败', isAuthError: error.isAuthError }
    }
  }

  const loginByUid = async (uid, username = null) => {
    try {
      const data = await userApi.loginByUid(uid, username)
      user.value = data
      localStorage.setItem('user', JSON.stringify(data))
      return { success: true, data }
    } catch (error) {
      return { success: false, error: error.message || '登录失败', isAuthError: error.isAuthError }
    }
  }

  const register = async (username, password) => {
    try {
      const data = await userApi.register(username, password)
      return { success: true, data }
    } catch (error) {
      return { success: false, error: error.message || '注册失败', isAuthError: error.isAuthError }
    }
  }

  const logout = () => {
    user.value = null
    localStorage.removeItem('user')
  }

  const loadUserFromStorage = () => {
    return new Promise((resolve, reject) => {
      const stored = localStorage.getItem('user')
      if (stored) {
        try {
          user.value = JSON.parse(stored)
        } catch (e) {
          console.error('Failed to parse stored user:', e)
        }
      }
      resolve()
    })
    
  }

  const setUserInfo = (data) => {
    user.value = data
    if (data) {
      localStorage.setItem('user', JSON.stringify(data))
    } else {
      localStorage.removeItem('user')
    }
  }

  const getUid = () => {
    return user.value?.uid || null
  }

  return {
    user,
    isLoggedIn,
    login,
    auth,
    loginByUid,
    register,
    logout,
    loadUserFromStorage,
    setUserInfo,
    getUid,
    openLoginModal
  }
})
