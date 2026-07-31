import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import * as Icons from '@element-plus/icons-vue'
import App from './App.vue'
import 'element-plus/theme-chalk/dark/css-vars.css'
import './styles/global.css'
import './styles/element-override.css'

const app = createApp(App)
for (const [k, c] of Object.entries(Icons)) app.component(k, c)
app.use(ElementPlus)
app.mount('#app')
