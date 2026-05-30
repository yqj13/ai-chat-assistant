import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useUserStore } from './stores/user'
import { useLogin } from './composables/useLogin.js'

import './assets/main.css'
// 引入组件库的少量全局样式变量
import 'tdesign-vue-next/es/style/index.css';


const app = createApp(App)

app.use(createPinia())
app.use(router)

// 注册登录指令
app.directive('login', {
    mounted(el, binding) {
        const userStore = useUserStore()
        el.addEventListener('click', () => {
            !userStore.getUid() && useLogin().open({
                onConfirm: (user) => {
                    userStore.setUserInfo(user)
                }
            })
        })
    }
})


app.mount('#app')
