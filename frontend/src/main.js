import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

import './assets/main.css'
// 代码高亮主题（Catppuccin Mocha 风格已内置，也可用这个）
import 'highlight.js/styles/atom-one-dark.css'

// KaTeX 样式
import 'katex/dist/katex.min.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
