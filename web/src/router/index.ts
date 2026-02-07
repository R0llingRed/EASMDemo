import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import DashboardView from '../views/DashboardView.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            component: MainLayout,
            children: [
                {
                    path: '',
                    name: 'dashboard',
                    component: DashboardView
                },
                {
                    path: 'projects',
                    name: 'projects',
                    component: () => import('../views/ProjectsView.vue')
                },
                {
                    path: 'assets',
                    name: 'assets',
                    component: () => import('../views/AssetsView.vue')
                },
                {
                    path: 'risks',
                    name: 'risks',
                    component: () => import('../views/RisksView.vue')
                },
                {
                    path: 'tasks',
                    name: 'tasks',
                    component: () => import('../views/TasksView.vue')
                },
                {
                    path: 'settings',
                    name: 'settings',
                    component: () => import('../views/SettingsView.vue')
                }
            ]
        }
    ]
})

export default router
