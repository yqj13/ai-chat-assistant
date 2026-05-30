// composables/useLogin.js
import { createVNode, render } from 'vue'
import LoginDialog from '@/components/LoginDialog.vue'

export function useLogin() {
  return {
    /**
     * 打开登录对话框
     * @param {Object} options
     * @param {string} [options.title] 对话框标题
     * @param {(user: any) => void} [options.onConfirm] 登录/注册成功回调，参数为后端返回的用户信息
     * @param {() => void} [options.onCancel] 取消登录回调
     */
    open({ title = '登录', onConfirm, onCancel } = {}) {
      const container = document.createElement('div')
      document.body.appendChild(container)

      function close() {
        render(null, container)
        if (container.parentNode) {
          container.parentNode.removeChild(container)
        }
      }

      const vnode = createVNode(LoginDialog, {
        title,
        onConfirm: (user) => {
          if (typeof onConfirm === 'function') {
            onConfirm(user)
          }
          close()
        },
        onCancel: () => {
          if (typeof onCancel === 'function') {
            onCancel()
          }
          close()
        }
      })

      render(vnode, container)

      return { close }
    }
  }
}
