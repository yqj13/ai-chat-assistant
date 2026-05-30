import { createApp, h } from 'vue'
import LoginModal from '@/components/LoginModal.vue'

let loginModalInstance = null
let loginModalContainer = null

/**
 * 打开登录模态框
 * @param {Function} onSuccess - 登录成功回调函数
 * @returns {Promise} 返回一个Promise，resolve登录结果，reject取消或错误
 */
export const openLoginModal = (onSuccess) => {
  return new Promise((resolve, reject) => {
    // 如果已经存在实例，直接显示
    if (loginModalInstance) {
      loginModalInstance.exposed.open()
      // 更新回调函数
      if (onSuccess) {
        loginModalInstance._props.onSuccess = onSuccess
      }
      return
    }

    // 创建容器元素
    loginModalContainer = document.createElement('div')
    loginModalContainer.id = 'login-modal-container'
    document.body.appendChild(loginModalContainer)

    // 创建Vue应用实例
    const app = createApp({
      data() {
        return {
          visible: true
        }
      },
      methods: {
        handleClose() {
          this.visible = false
          // 移除DOM元素
          if (loginModalContainer && loginModalContainer.parentNode) {
            loginModalContainer.parentNode.removeChild(loginModalContainer)
          }
          loginModalInstance = null
          loginModalContainer = null
          reject(new Error('Login cancelled'))
        },
        handleSuccess(user) {
          this.visible = false
          // 移除DOM元素
          if (loginModalContainer && loginModalContainer.parentNode) {
            loginModalContainer.parentNode.removeChild(loginModalContainer)
          }
          loginModalInstance = null
          loginModalContainer = null
          if (onSuccess) {
            onSuccess(user)
          }
          resolve(user)
        }
      },
      render() {
        return h(LoginModal, {
          visible: this.visible,
          'onUpdate:visible': (val) => {
            if (!val) {
              this.handleClose()
            }
          },
          onSuccess: this.handleSuccess
        })
      }
    })

    // 挂载应用
    loginModalInstance = app.mount(loginModalContainer)
  })
}

/**
 * 关闭登录模态框
 */
export const closeLoginModal = () => {
  if (loginModalInstance) {
    loginModalInstance.visible = false
    if (loginModalContainer && loginModalContainer.parentNode) {
      loginModalContainer.parentNode.removeChild(loginModalContainer)
    }
    loginModalInstance = null
    loginModalContainer = null
  }
}