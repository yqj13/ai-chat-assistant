<!-- components/LoginDialog.vue -->
<template>
  <Teleport to="body">
    <div v-if="visible" class="dialog-overlay" @click.self="onCancel">
      <div class="dialog-box">
        <div class="dialog-header">
          <div class="logo">
            <robot-2-icon :fill-color="'transparent'" :stroke-color="'#1890ff'" :stroke-width="2" />
            <span>AI 聊天助手</span>
          </div>
          <h3>{{ isLoginMode ? '欢迎回来' : '创建账户' }}</h3>
          <p>{{ isLoginMode ? '登录您的账户开始聊天' : '注册新账户' }}</p>
        </div>

        <form class="dialog-content" @submit.prevent="onConfirm">
          <div class="form-group">
            <label class="form-label">
              <user-icon :fill-color="'transparent'" :stroke-color="'#999'" :stroke-width="1.5" />
              用户名
            </label>
            <t-input
              v-model="username"
              placeholder="请输入用户名"
              :disabled="loading"
            />
          </div>

          <div class="form-group">
            <label class="form-label">
              <lock-on-icon :fill-color="'transparent'" :stroke-color="'#999'" :stroke-width="1.5" />
              密码
            </label>
            <t-input
              v-model="password"
              type="password"
              placeholder="请输入密码"
              :disabled="loading"
            />
          </div>

          <div v-if="!isLoginMode" class="form-group">
            <label class="form-label">
              <lock-on-icon :fill-color="'transparent'" :stroke-color="'#999'" :stroke-width="1.5" />
              确认密码
            </label>
            <t-input
              v-model="confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              :disabled="loading"
            />
            <div v-if="password && confirmPassword && password !== confirmPassword" class="error-hint">
              两次输入的密码不一致
            </div>
          </div>

          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>
        </form>

        <div class="dialog-actions">
          <t-button
            variant="outline"
            :disabled="loading"
            @click="onGuest"
          >
            游客模式
          </t-button>
          <t-button
            type="primary"
            :loading="loading"
            :disabled="!canSubmit || loading"
            @click="onConfirm"
          >
            {{ isLoginMode ? '登录' : '注册' }}
          </t-button>
        </div>

        <div class="dialog-footer">
          <span>{{ isLoginMode ? '还没有账户？' : '已有账户？' }}</span>
          <button class="mode-toggle" @click="toggleMode">
            {{ isLoginMode ? '立即注册' : '立即登录' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'
import { UserIcon, LockOnIcon, Robot2Icon } from 'tdesign-icons-vue-next'
import { Button as TButton, Input as TInput } from 'tdesign-vue-next'
import { userApi } from '../api/user'

const props = defineProps({
  title: {
    type: String,
    default: '登录'
  },
  onConfirm: {
    type: Function,
    required: true
  },
  onCancel: {
    type: Function,
    required: true
  }
})

const visible = ref(true)
const isLoginMode = ref(true)
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const errorMessage = ref('')
const loading = ref(false)

const canSubmit = computed(() => {
  if (isLoginMode.value) {
    return username.value.trim() && password.value.trim()
  }
  return (
    username.value.trim() &&
    password.value.trim() &&
    password.value === confirmPassword.value
  )
})

function toggleMode() {
  isLoginMode.value = !isLoginMode.value
  errorMessage.value = ''
  confirmPassword.value = ''
}

async function onConfirm() {
  if (!canSubmit.value || loading.value) return
  errorMessage.value = ''
  loading.value = true
  try {
    let result
    if (isLoginMode.value) {
      result = await userApi.login(username.value, password.value)
    } else {
      result = await userApi.register(username.value, password.value)
      if (result && !result.error) {
        result = await userApi.login(username.value, password.value)
      } else {
        throw new Error(result?.error || '注册失败')
      }
    }

    if (result && !result.error) {
      localStorage.setItem('user', JSON.stringify(result))
      props.onConfirm(result)
      visible.value = false
    } else {
      errorMessage.value = result?.error || '操作失败'
    }
  } catch (error) {
    errorMessage.value = error.message || '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function onGuest() {
  if (loading.value) return
  errorMessage.value = ''
  loading.value = true
  try {
    const guestUid =
      'guest_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
    const result = await userApi.loginByUid(guestUid, '游客')
    if (result && !result.error) {
      localStorage.setItem('user', JSON.stringify(result))
      props.onConfirm(result)
      visible.value = false
    } else {
      errorMessage.value = result?.error || '登录失败'
    }
  } catch (error) {
    errorMessage.value = error.message || '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}

function onCancel() {
  if (loading.value) return
  props.onCancel()
  visible.value = false
}
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.dialog-box {
  background: white;
  border-radius: 12px;
  padding: 24px;
  min-width: 360px;
  max-width: 420px;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.dialog-header {
  text-align: center;
  margin-bottom: 20px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 700;
  color: #1890ff;
  margin-bottom: 12px;
}

.logo svg {
  width: 32px;
  height: 32px;
}

.dialog-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin: 0 0 6px 0;
}

.dialog-header p {
  font-size: 13px;
  color: #999;
  margin: 0;
}

.dialog-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #333;
}

.form-label svg {
  width: 14px;
  height: 14px;
}

.error-hint {
  font-size: 12px;
  color: #f5222d;
}

.error-message {
  padding: 8px 10px;
  background: #fff2f0;
  border-radius: 6px;
  color: #f5222d;
  font-size: 13px;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 18px;
}

.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 16px;
  font-size: 13px;
  color: #666;
}

.mode-toggle {
  color: #1890ff;
  cursor: pointer;
  font-weight: 500;
  background: none;
  border: none;
  padding: 0;
}

.mode-toggle:hover {
  text-decoration: underline;
}
</style>
