import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import HomePage from './components/HomePage.vue'
import ChatPage from './components/ChatPage.vue'
import AnalyticsPage from './components/AnalyticsPage.vue'
import SourcesPage from './components/SourcesPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomePage },
    { path: '/chat', component: ChatPage },
    { path: '/analytics', component: AnalyticsPage },
    { path: '/sources', component: SourcesPage }
  ]
})

const app = createApp(App)
app.use(router)
app.mount('#app') 