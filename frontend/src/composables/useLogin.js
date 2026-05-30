// composables/useLogin.js
import { createVNode, render } from 'vue'
import LoginDialog from '@/components/LoginDialog.vue'

let activeInstance = null

function destroy() {
  if (!activeInstance) return
  const { container } = activeInstance
  try {
    render(null, container)
  } catch (e) {
    console.error('[useLogin] unmount error:', e)
  }
  if (container.parentNode) {
    container.parentNode.removeChild(container)
  }
  activeInstance = null
}

export function useLogin() {
  return {
    /**
     * 打开登录对话框（全局单例：若已有打开的弹窗，直接复用，不会重复打开）
     * @param {Object} options
     * @param {string} [options.title] 对话框标题
     * @param {(user: any) => void} [options.onConfirm] 登录/注册成功回调
     * @param {() => void} [options.onCancel] 取消登录回调
     */
    open({ title = '登录', onConfirm, onCancel } = {}) {
      if (activeInstance) {
        // 单例模式：复用已有弹窗，并刷新回调
        activeInstance.callbacks.onConfirm = onConfirm
        activeInstance.callbacks.onCancel = onCancel
        return { close: destroy }
      }

      const container = document.createElement('div')
      document.body.appendChild(container)

      const callbacks = { onConfirm, onCancel }

      const vnode = createVNode(LoginDialog, {
        title,
        onConfirm: (user) => {
          const cb = callbacks.onConfirm
          destroy()
          if (typeof cb === 'function') cb(user)
        },
        onCancel: () => {
          const cb = callbacks.onCancel
          destroy()
          if (typeof cb === 'function') cb()
        }
      })

      activeInstance = { container, vnode, callbacks }
      render(vnode, container)

      return { close: destroy }
    },

    /** 主动关闭当前弹窗 */
    close: destroy,

    /** 当前是否已存在登录弹窗 */
    isOpen() {
      return !!activeInstance
    }
  }
}
