import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'

import 'element-plus/theme-chalk/dark/css-vars.css'
import './styles/global.css'
import './styles/element-dark.css'

const app = createApp(App)

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus)
app.mount('#app')
