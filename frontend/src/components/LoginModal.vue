<script setup>
import { ref, computed, watch } from 'vue'
import { UserIcon, LockOnIcon, MailIcon, Robot2Icon } from 'tdesign-icons-vue-next'
import { Button as TButton, Input as TInput } from 'tdesign-vue-next'
import { userApi } from '../api/user'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible', 'success'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const isLoginMode = ref(true)
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const errorMessage = ref('')
const isLoading = ref(false)

const canSubmit = computed(() => {
  if (isLoginMode.value) {
    return username.value.trim() && password.value.trim()
  }
  return username.value.trim() && password.value.trim() && password.value === confirmPassword.value
})

const handleSubmit = async () => {
  errorMessage.value = ''
  isLoading.value = true

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
      emit('success', result)
      handleClose()
    } else {
      errorMessage.value = result?.error || '操作失败'
    }
  } catch (error) {
    errorMessage.value = error.message || '网络错误，请稍后重试'
  } finally {
    isLoading.value = false
  }
}

const handleGuestLogin = async () => {
  errorMessage.value = ''
  isLoading.value = true

  try {
    const guestUid = 'guest_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
    const result = await userApi.loginByUid(guestUid, '游客')
    
    if (result && !result.error) {
      localStorage.setItem('user', JSON.stringify(result))
      emit('success', result)
      handleClose()
    } else {
      errorMessage.value = result?.error || '登录失败'
    }
  } catch (error) {
    errorMessage.value = error.message || '网络错误，请稍后重试'
  } finally {
    isLoading.value = false
  }
}

const toggleMode = () => {
  isLoginMode.value = !isLoginMode.value
  errorMessage.value = ''
  confirmPassword.value = ''
}

const handleClose = () => {
  dialogVisible.value = false
  username.value = ''
  password.value = ''
  confirmPassword.value = ''
  errorMessage.value = ''
}

const open = () => {
  dialogVisible.value = true
}

// 添加close方法，以便外部可以关闭模态框
const close = () => {
  handleClose()
}

defineExpose({
  open,
  close
})

watch(() => props.visible, (val) => {
  if (!val) {
    username.value = ''
    password.value = ''
    confirmPassword.value = ''
    errorMessage.value = ''
  }
})
</script>

<template>
  <t-dialog
    v-model:visible="dialogVisible"
    :close-on-overlay-click="false"
    :close-on-esc-keydown="false"
    header="登录"
    mode="modal"
    :footer="false"
    width="420px"
    style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);"
     >
    <div class="login-modal">
      <div class="login-header">
        <div class="logo">
          <robot-2-icon :fill-color="'transparent'" :stroke-color="'#1890ff'" :stroke-width="2" />
          <span>AI 聊天助手</span>
        </div>
        <h2>{{ isLoginMode ? '欢迎回来' : '创建账户' }}</h2>
        <p>{{ isLoginMode ? '登录您的账户开始聊天' : '注册新账户' }}</p>
      </div>

      <form class="login-form" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label class="form-label">
            <user-icon :fill-color="'transparent'" :stroke-color="'#999'" :stroke-width="1.5" />
            用户名
          </label>
          <t-input
            v-model="username"
            placeholder="请输入用户名"
            :disabled="isLoading"
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
            :disabled="isLoading"
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
            :disabled="isLoading"
          />
          <div v-if="password && confirmPassword && password !== confirmPassword" class="error-hint">
            两次输入的密码不一致
          </div>
        </div>

        <div v-if="errorMessage" class="error-message">
          <mail-icon :fill-color="'transparent'" :stroke-color="'#f5222d'" :stroke-width="1.5" />
          {{ errorMessage }}
        </div>

        <t-button
          type="primary"
          class="submit-btn"
          :disabled="!canSubmit || isLoading"
          :loading="isLoading"
          @click="handleSubmit"
        >
          {{ isLoginMode ? '登录' : '注册' }}
        </t-button>

        <t-button
          variant="outline"
          class="guest-btn"
          :disabled="isLoading"
          @click="handleGuestLogin"
        >
          游客模式登录
        </t-button>
      </form>

      <div class="login-footer">
        <span>{{ isLoginMode ? '还没有账户？' : '已有账户？' }}</span>
        <button class="mode-toggle" @click="toggleMode">
          {{ isLoginMode ? '立即注册' : '立即登录' }}
        </button>
      </div>
    </div>
  </t-dialog>
</template>

<style scoped>
.login-modal {
  padding: 8px;

}

.login-header {
  text-align: center;
  margin-bottom: 24px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 20px;
  font-weight: 700;
  color: #1890ff;
  margin-bottom: 16px;
}

.logo svg {
  width: 36px;
  height: 36px;
}

.login-header h2 {
  font-size: 22px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
}

.login-header p {
  font-size: 14px;
  color: #999;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
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
  font-size: 14px;
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
  margin-top: -2px;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px;
  background: #fff2f0;
  border-radius: 6px;
  color: #f5222d;
  font-size: 13px;
}

.error-message svg {
  width: 14px;
  height: 14px;
}

.submit-btn {
  height: 44px;
  font-size: 15px;
  font-weight: 500;
  border-radius: 8px;
}

.guest-btn {
  height: 44px;
  font-size: 14px;
  border-radius: 8px;
}

.login-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 20px;
  font-size: 14px;
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