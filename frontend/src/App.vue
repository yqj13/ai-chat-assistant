<script setup>
import { RouterView } from 'vue-router'
import { useLogin } from './composables/useLogin'
import { onMounted } from 'vue'
import { useUserStore } from './stores/user'

const userStore = useUserStore()

onMounted(async () => {
  // 先把 localStorage 中的用户恢复到 store，再判断是否需要弹登录框
  await userStore.loadUserFromStorage()

  if (!userStore.getUid()) {
    useLogin().open({
      onConfirm: (user) => {
        userStore.setUserInfo(user)
      }
    })
  }
})
</script>

<template>
  <RouterView />
</template>

<style>
html, body, #app {
  height: 100%;
  margin: 0;
  padding: 0;
}
</style>