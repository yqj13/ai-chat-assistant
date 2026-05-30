import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userApi } from '../api/user'
import { setLoginModalInstance } from '../utils/request'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const loginModalRef = ref(null)
  const isLoggedIn = computed(() => !!user.value?.uid)

  const setLoginModal = (modalRef) => {
    loginModalRef.value = modalRef
    if (modalRef) {
      setLoginModalInstance(modalRef)
    }
  }

  const openLoginModal = () => {
    if (loginModalRef.value) {
      loginModalRef.value.open()
    }
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
    const stored = localStorage.getItem('user')
    if (stored) {
      try {
        user.value = JSON.parse(stored)
      } catch (e) {
        console.error('Failed to parse stored user:', e)
      }
    }
  }

  const getUid = () => {
    return user.value?.uid || null
  }

  return {
    user,
    isLoggedIn,
    login,
    loginByUid,
    register,
    logout,
    loadUserFromStorage,
    getUid,
    setLoginModal,
    openLoginModal
  }
})