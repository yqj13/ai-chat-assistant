import { createRouter, createWebHistory } from 'vue-router'
import ChatPage from '../views/ChatPage.vue'

const routes = [
  {
    path: '/',
    name: 'chat',
    component: ChatPage
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router