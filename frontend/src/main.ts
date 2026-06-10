import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import HomeView from './views/HomeView.vue'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomeView },
    { path: '/chat', component: () => import('./views/HomeView.vue') },
    { path: '/kb', component: () => import('./views/KBView.vue') },
    { path: '/graph', component: () => import('./views/GraphView.vue') },
  ],
})

createApp(App).use(router).mount('#app')
