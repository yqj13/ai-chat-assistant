<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import LoginModal from '../components/LoginModal.vue'
import { Button as TButton } from 'tdesign-vue-next'
import { Robot2Icon } from 'tdesign-icons-vue-next'

const router = useRouter()
const userStore = useUserStore()
const loginModalVisible = ref(false)
const loginModalRef = ref(null)

onMounted(() => {
  userStore.setLoginModal(loginModalRef.value)
  
  if (userStore.isLoggedIn) {
    router.push('/')
  }
})

const openLogin = () => {
  loginModalVisible.value = true
}

const handleLoginSuccess = (userData) => {
  console.log('[LoginPage] Login success:', userData)
  router.push('/')
}

const guestLogin = async () => {
  const guestUid = 'guest_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
  const result = await userStore.loginByUid(guestUid, '游客')
  
  if (result.success) {
    router.push('/')
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <div class="logo">
          <robot-2-icon :fill-color="'transparent'" :stroke-color="'#1890ff'" :stroke-width="2" />
          <span>AI 聊天助手</span>
        </div>
        <h1>欢迎使用 AI 聊天助手</h1>
        <p>智能对话，触手可及</p>
      </div>

      <div class="login-actions">
        <t-button
          type="primary"
          size="large"
          class="login-btn"
          @click="openLogin"
        >
          开始使用
        </t-button>

        <t-button
          variant="outline"
          size="large"
          class="guest-btn"
          @click="guestLogin"
        >
          游客模式
        </t-button>
      </div>

      <div class="features">
        <div class="feature-item">
          <div class="feature-icon">💬</div>
          <div class="feature-text">智能对话</div>
        </div>
        <div class="feature-item">
          <div class="feature-icon">🔍</div>
          <div class="feature-text">联网搜索</div>
        </div>
        <div class="feature-item">
          <div class="feature-icon">🧠</div>
          <div class="feature-text">深度思考</div>
        </div>
      </div>
    </div>

    <LoginModal
      ref="loginModalRef"
      v-model:visible="loginModalVisible"
      @success="handleLoginSuccess"
    />
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-container {
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 48px;
  width: 100%;
  max-width: 480px;
  text-align: center;
}

.login-header {
  margin-bottom: 40px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 28px;
  font-weight: 700;
  color: #1890ff;
  margin-bottom: 24px;
}

.logo svg {
  width: 48px;
  height: 48px;
}

.login-header h1 {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  margin: 0 0 12px 0;
}

.login-header p {
  font-size: 16px;
  color: #999;
  margin: 0;
}

.login-actions {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 40px;
}

.login-btn {
  height: 52px;
  font-size: 18px;
  font-weight: 500;
  border-radius: 12px;
}

.guest-btn {
  height: 52px;
  font-size: 16px;
  border-radius: 12px;
}

.features {
  display: flex;
  justify-content: center;
  gap: 32px;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.feature-icon {
  font-size: 32px;
}

.feature-text {
  font-size: 14px;
  color: #666;
}

@media (max-width: 480px) {
  .login-container {
    padding: 32px 24px;
  }

  .login-header h1 {
    font-size: 24px;
  }

  .logo {
    font-size: 24px;
  }

  .features {
    gap: 20px;
  }
}
</style>